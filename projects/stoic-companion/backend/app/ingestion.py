import argparse
import hashlib
import json
import time
import uuid
import zipfile

import httpx
from sqlalchemy import select

from .chunking import normalize, parse_letter, parse_text, split_spans
from .config import ROOT, settings
from .db import Chunk, IngestionJob, Passage, Session, Source, init_db
from .vectors import Embeddings, VectorStore

MANIFEST = ROOT / "corpus/sources.json"


def manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def checksum(raw):
    return hashlib.sha256(raw).hexdigest()


def download(item):
    path = settings.data_dir / "raw" / item["filename"]
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = ROOT / "corpus/snapshots.zip"
    if not path.exists() and snapshot.exists():
        with zipfile.ZipFile(snapshot) as archive:
            if item["filename"] in archive.namelist():
                path.write_bytes(archive.read(item["filename"]))
    if not path.exists():
        response = httpx.get(
            item["download_url"],
            follow_redirects=True,
            timeout=60,
            headers={"User-Agent": "StoicCompanion/1.0 (public-domain research; one request per second)"},
        )
        response.raise_for_status()
        path.write_bytes(response.content)
        time.sleep(1)
    raw = path.read_bytes()
    if checksum(raw) != item["source_checksum"]:
        raise ValueError(f"Checksum drift: {item['id']}. Review source changes and update manifest explicitly.")
    return raw


def units(item, raw):
    text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    # Some Gutenberg responses contain doubled CR; collapse blank runs only.
    import re

    text = re.sub(r"\n{3,}", "\n\n", text)
    return parse_letter(text, item["letter_number"]) if item["parser"] == "letter" else parse_text(item["work"], text)


def ingest(item, store):
    if item["ingestion_status"] != "approved":
        return {"source": item["id"], "status": "blocked", "reason": item["rights_justification"]}
    raw = download(item)
    parsed = units(item, raw)
    with Session() as db:
        source = db.get(Source, item["id"])
        job = IngestionJob(source_id=item["id"])
        db.add(job)
        db.commit()
        try:
            version_suffix = ":" + settings.corpus_version if settings.corpus_version != "v1" else ""
            signature = checksum(
                (item["source_checksum"] + settings.chunk_strategy + ":parser-v1" + version_suffix).encode()
            )
            if source and source.checksum != signature:
                raise ValueError(
                    "Source or chunking changed; use a fresh database/collection to preserve existing citations"
                )
            if not source:
                source = Source(id=item["id"], metadata_json=item, checksum=signature, status="indexing")
                db.add(source)
                db.flush()
                for reference, text, meta in parsed:
                    # Bound very long parents; keep original reference on every subdivision.
                    for part, (ps, pe) in enumerate(split_spans(text, target=1300)):
                        pid = f"{item['id']}:{reference}" + (f":part{part + 1}" if ps or pe < len(text) else "")
                        parent_text = text[ps:pe]
                        metadata = {
                            k: item.get(k) for k in ("author", "work", "title", "translator", "edition", "source_url")
                        }
                        metadata.update(
                            book_number=None,
                            chapter_number=None,
                            section_number=None,
                            letter_number=None,
                            semantic_topics=[],
                            document_id=item["id"],
                            corpus_version=settings.corpus_version,
                            unit_start=ps,
                            unit_end=pe,
                        )
                        metadata.update(meta)
                        db.add(Passage(id=pid, source_id=item["id"], quote_text=parent_text, metadata_json=metadata))
                        db.flush()
                        for a, b in split_spans(parent_text, settings.chunk_strategy):
                            quote = parent_text[a:b]
                            cid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{pid}:{a}:{b}:{checksum(quote.encode())}"))
                            db.add(
                                Chunk(
                                    id=cid,
                                    parent_id=pid,
                                    quote_text=quote,
                                    search_text=normalize(quote),
                                    start=a,
                                    end=b,
                                    metadata_json={**metadata, "text_hash": checksum(quote.encode())},
                                )
                            )
                db.commit()
            chunks = list(db.scalars(select(Chunk).join(Passage).where(Passage.source_id == item["id"])))
            embeddings = Embeddings().embed([c.search_text for c in chunks])
            # Deterministic point IDs make retry after a partial upsert safe.
            store.upsert(chunks, embeddings)
            source.status = "indexed"
            job.status = "complete"
            job.detail = f"{len(parsed)} units; {len(chunks)} chunks"
            db.commit()
            normalized = settings.data_dir / "normalized"
            normalized.mkdir(exist_ok=True)
            (normalized / (item["id"] + ".txt")).write_text("\n\n".join(t for _, t, _ in parsed), encoding="utf-8")
            return {"source": item["id"], "status": "indexed", "units": len(parsed), "chunks": len(chunks)}
        except Exception as exc:
            db.rollback()
            saved = db.get(IngestionJob, job.id)
            if saved:
                saved.status = "failed"
                saved.detail = type(exc).__name__
                db.commit()
            raise


def validate():
    count = 0
    with Session() as db:
        for c in db.scalars(select(Chunk)):
            p = db.get(Passage, c.parent_id)
            assert p and p.quote_text[c.start : c.end] == c.quote_text, c.id
            assert checksum(c.quote_text.encode()) == c.metadata_json["text_hash"]
            count += 1
    for item in manifest():
        if item["ingestion_status"] == "approved":
            download(item)
    return {"validated_chunks": count, "checksums": "verified"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["ingest", "status", "validate"])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--work")
    args = parser.parse_args()
    init_db()
    if args.command == "validate":
        print(json.dumps(validate(), indent=2))
    elif args.command == "status":
        with Session() as db:
            print(
                json.dumps(
                    [
                        {
                            "id": i["id"],
                            "approval": i["ingestion_status"],
                            "status": (s.status if (s := db.get(Source, i["id"])) else "not ingested"),
                        }
                        for i in manifest()
                    ],
                    indent=2,
                )
            )
    else:
        if not args.all and not args.work:
            parser.error("Specify --all or --work")
        chosen = [i for i in manifest() if args.all or i["work"] == args.work]
        if not chosen:
            parser.error("Unknown work")
        store = VectorStore()
        try:
            for i in chosen:
                print(json.dumps(ingest(i, store)))
        finally:
            store.close()


if __name__ == "__main__":
    main()
