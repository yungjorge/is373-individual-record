import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select

from .auth import Principal, admin, guest_token, principal, valid_guest
from .config import settings
from .db import Bookmark, Conversation, Message, Passage, Session, Source, Usage, User, init_db
from .generation import GenerationFailure, assemble, generate, rewrite, safety_message
from .ingestion import ingest, manifest
from .retrieval import retrieve
from .vectors import Embeddings, VectorStore

log = logging.getLogger(__name__)
rates = defaultdict(deque)
active = set()
budget_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app):
    settings.validate_runtime()
    init_db()
    app.state.store = VectorStore()
    yield
    app.state.store.close()


app = FastAPI(title="Stoic Companion", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(HTTPException)
async def http_error(_, exc):
    return JSONResponse({"error": {"code": exc.status_code, "message": exc.detail}}, status_code=exc.status_code)


def user(db, p):
    if not db.get(User, p.id):
        db.add(User(id=p.id))
        db.commit()


def owned(db, cid, p):
    c = db.get(Conversation, cid)
    if not c or c.user_id != p.id:
        raise HTTPException(404, "Conversation not found")
    return c


class ChatInput(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
    author: str | None = Field(default=None, max_length=100)
    work: str | None = Field(default=None, max_length=80)


@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "embedding_provider": settings.embedding_provider,
        "generation_provider": "demo" if settings.use_demo_generation else "openai",
        "chat_model": "offline-template" if settings.use_demo_generation else settings.chat_model,
        "corpus_version": settings.corpus_version,
        "debug_enabled": settings.debug_enabled and settings.demo_mode,
    }


@app.get("/api/v1/ready")
def ready():
    with Session() as db:
        count = db.scalar(select(func.count()).select_from(Passage))
    if not count:
        raise HTTPException(503, "Run source ingestion first")
    vector = Embeddings().embed(["readiness"])[0]
    app.state.store.ensure(len(vector))
    if not app.state.store.client.get_collection(app.state.store.collection).points_count:
        raise HTTPException(503, "Vector collection is empty; run ingestion")
    return {"status": "ready", "passages": count}


@app.post("/api/v1/demo-session")
def demo_session(response: Response, stoic_guest: str | None = Cookie(default=None)):
    if not settings.demo_mode:
        raise HTTPException(404, "Demo is disabled")
    if not valid_guest(stoic_guest):
        response.set_cookie("stoic_guest", guest_token(), httponly=True, samesite="lax", max_age=86400)
    return {"mode": "demo", "message_limit": settings.guest_message_limit, "expires_in": 86400}


@app.post("/api/v1/conversations", status_code=201)
def create_conversation(p: Principal = Depends(principal)):
    with Session() as db:
        user(db, p)
        c = Conversation(user_id=p.id)
        db.add(c)
        db.commit()
        return {"id": c.id, "title": c.title}


@app.get("/api/v1/conversations")
def conversations(p: Principal = Depends(principal)):
    with Session() as db:
        return [
            {"id": c.id, "title": c.title, "created_at": c.created_at}
            for c in db.scalars(
                select(Conversation)
                .where(Conversation.user_id == p.id)
                .order_by(Conversation.created_at.desc())
                .limit(100)
            )
        ]


@app.get("/api/v1/conversations/{cid}")
def conversation(cid: str, p: Principal = Depends(principal)):
    with Session() as db:
        c = owned(db, cid, p)
        return {
            "id": c.id,
            "title": c.title,
            "messages": [
                {"id": m.id, "role": m.role, "content": m.content, "result": m.result}
                for m in db.scalars(select(Message).where(Message.conversation_id == cid).order_by(Message.created_at))
            ],
        }


@app.delete("/api/v1/conversations/{cid}", status_code=204)
def delete_conversation(cid: str, p: Principal = Depends(principal)):
    if cid in active:
        raise HTTPException(409, "Conversation is processing a message")
    with Session() as db:
        db.delete(owned(db, cid, p))
        db.commit()


@app.post("/api/v1/conversations/{cid}/messages")
async def message(cid: str, data: ChatInput, p: Principal = Depends(principal)):
    if not data.message.strip():
        raise HTTPException(422, "Message cannot be blank")
    with Session() as db:
        owned(db, cid, p)
        history = [
            {"role": m.role, "content": m.content}
            for m in db.scalars(
                select(Message).where(Message.conversation_id == cid).order_by(Message.created_at.desc()).limit(8)
            )
        ][::-1]
        if p.guest:
            count = db.scalar(
                select(func.count())
                .select_from(Message)
                .join(Conversation)
                .where(Conversation.user_id == p.id, Message.role == "user")
            )
            if count >= settings.guest_message_limit:
                raise HTTPException(429, "Demo message limit reached")
    stamp = time.monotonic()
    queue = rates[p.id]
    while queue and queue[0] < stamp - 60:
        queue.popleft()
    if len(queue) >= settings.requests_per_minute:
        raise HTTPException(429, "Please wait before sending another message")
    if cid in active:
        raise HTTPException(409, "A reply is already in progress")
    queue.append(stamp)
    active.add(cid)

    async def events():
        def event(name, payload):
            return "event: " + name + "\ndata: " + json.dumps(payload, ensure_ascii=False) + "\n\n"

        try:
            yield event("status", {"message": "Finding relevant passages…"})
            query = rewrite(data.message, history)
            begin = time.perf_counter()

            def search():
                with Session() as db:
                    return retrieve(db, app.state.store, query, data.author, data.work)

            if safety_message(data.message):
                evidence, debug = [], {"strategies": ["safety"], "timing_ms": 0}
            else:
                evidence, debug = await asyncio.to_thread(search)
            yield event("status", {"message": "Preparing a grounded reflection…"})
            generation_start = time.perf_counter()
            # Single-process lock keeps local global spend guard from concurrent overshoot.
            async with budget_lock:
                with Session() as db:
                    month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    spent = db.scalar(select(func.sum(Usage.estimated_cost)).where(Usage.created_at >= month)) or 0
                    reserve = (
                        0
                        if settings.use_demo_generation or safety_message(data.message)
                        else (
                            2
                            * (
                                20000 * settings.input_usd_per_million
                                + settings.max_output_tokens * settings.output_usd_per_million
                            )
                        )
                        / 1e6
                    )
                    if spent + reserve > settings.monthly_budget_usd:
                        raise HTTPException(429, "Configured monthly spending guard reached")
                try:
                    answer, usage = await asyncio.to_thread(generate, data.message, history, evidence)
                except GenerationFailure as exc:
                    with Session() as db:
                        db.add(Usage(user_id=p.id, **exc.usage))
                        db.commit()
                    raise
                with Session() as db:
                    db.add(Usage(user_id=p.id, **usage))
                    db.commit()
                result = assemble(answer, evidence)
                debug.update(
                    original_query=data.message,
                    rewritten_query=query,
                    retrieved_passage_ids=[e["passage_id"] for e in evidence],
                    generation_ms=round((time.perf_counter() - generation_start) * 1000, 2),
                    total_ms=round((time.perf_counter() - begin) * 1000, 2),
                    usage=usage,
                )
                if settings.demo_mode and settings.debug_enabled:
                    result["debug"] = debug
                result["mode"] = "demo" if settings.use_demo_generation else "openai"
                with Session() as db:
                    c = owned(db, cid, p)
                    if c.title == "A new reflection":
                        c.title = data.message[:80]
                    db.add_all(
                        [
                            Message(conversation_id=cid, role="user", content=data.message),
                            Message(conversation_id=cid, role="assistant", content=answer.summary, result=result),
                        ]
                    )
                    db.commit()
            # Stream only validated prose. Citations arrive atomically with trusted metadata.
            for offset in range(0, len(answer.summary), 28):
                yield event("delta", {"text": answer.summary[offset : offset + 28]})
                await asyncio.sleep(0.008)
            yield event("result", result)
            yield event("done", {})
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.warning("Chat failed: %s", type(exc).__name__)
            yield event(
                "error",
                {
                    "message": exc.detail
                    if isinstance(exc, HTTPException)
                    else "The reflection could not be completed. Please retry. No unverified answer was saved."
                },
            )
        finally:
            active.discard(cid)

    return StreamingResponse(
        events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.get("/api/v1/sources")
def sources(q: str = "", author: str | None = None, work: str | None = None, offset: int = 0):
    if len(q) > 200 or offset < 0:
        raise HTTPException(422, "Invalid search")
    with Session() as db:
        query = select(Passage)
        if q:
            query = query.where(Passage.quote_text.ilike("%" + q + "%"))
        rows = db.scalars(query.order_by(Passage.id)).all()
        rows = [
            r
            for r in rows
            if (not author or r.metadata_json["author"] == author) and (not work or r.metadata_json["work"] == work)
        ]
        return {
            "catalog": [{"id": s.id, "status": s.status, **s.metadata_json} for s in db.scalars(select(Source))],
            "candidates": [i for i in manifest() if i["ingestion_status"] == "blocked"],
            "total": len(rows),
            "passages": [
                {"id": r.id, "quote_text": r.quote_text, **r.metadata_json} for r in rows[offset : offset + 30]
            ],
        }


@app.get("/api/v1/sources/{source_id}")
def source_detail(source_id: str):
    with Session() as db:
        s = db.get(Source, source_id)
        if not s:
            raise HTTPException(404, "Source not found")
        return {"id": s.id, "status": s.status, **s.metadata_json}


@app.get("/api/v1/passages/{pid}")
def passage(pid: str):
    with Session() as db:
        row = db.get(Passage, pid)
        if not row:
            raise HTTPException(404, "Passage not found")
        return {"id": row.id, "quote_text": row.quote_text, **row.metadata_json}


@app.get("/api/v1/bookmarks")
def bookmarks(p: Principal = Depends(principal)):
    with Session() as db:
        return [
            {"id": r.id, "quote_text": r.quote_text, **r.metadata_json}
            for r in db.scalars(select(Passage).join(Bookmark).where(Bookmark.user_id == p.id))
        ]


@app.post("/api/v1/bookmarks/{pid}", status_code=201)
def bookmark(pid: str, p: Principal = Depends(principal)):
    with Session() as db:
        user(db, p)
        if not db.get(Passage, pid):
            raise HTTPException(404, "Passage not found")
        if not db.get(Bookmark, (p.id, pid)):
            db.add(Bookmark(user_id=p.id, passage_id=pid))
            db.commit()
        return {"passage_id": pid}


@app.delete("/api/v1/bookmarks/{pid}", status_code=204)
def remove_bookmark(pid: str, p: Principal = Depends(principal)):
    with Session() as db:
        db.execute(delete(Bookmark).where(Bookmark.user_id == p.id, Bookmark.passage_id == pid))
        db.commit()


@app.post("/api/v1/debug/retrieve")
def debug_retrieve(data: ChatInput, p: Principal = Depends(principal)):
    if not settings.demo_mode or not settings.debug_enabled:
        raise HTTPException(403, "Debug disabled")
    with Session() as db:
        hits, debug = retrieve(db, app.state.store, data.message, data.author, data.work)
        return {"evidence": hits, "debug": debug}


@app.post("/api/v1/admin/ingest/{work}", dependencies=[Depends(admin)])
def admin_ingest(work: str):
    if active:
        raise HTTPException(409, "Wait for active chats to finish")
    chosen = [i for i in manifest() if i["work"] == work]
    if not chosen:
        raise HTTPException(404, "Unknown work")
    return [ingest(i, app.state.store) for i in chosen]
