"""Audit SQL/Qdrant consistency without exposing connection strings or credentials."""

import argparse
import json
import uuid
from pathlib import Path

from sqlalchemy import func, select, text

from .config import settings
from .db import Chunk, Passage, Session, Source, engine
from .generation import verify_quote
from .ingestion import checksum, validate
from .retrieval import retrieve
from .vectors import Embeddings, VectorStore

SCENARIO = "I worked extremely hard for a promotion, but another employee got it. I feel jealous and like my work was wasted. What would the Stoics recommend?"


def audit(require_services=True):
    if require_services and (engine.dialect.name != "postgresql" or not settings.qdrant_url):
        raise ValueError("This audit requires PostgreSQL and a Qdrant server, not local substitutes")
    result = {
        "database_dialect": engine.dialect.name,
        "corpus_version": settings.corpus_version,
        "embedding_provider": settings.embedding_provider,
        "generation_provider": "demo" if settings.use_demo_generation else "openai",
        "integrity": validate(),
    }
    with Session() as db:
        assert db.scalar(text("SELECT 1")) == 1
        result["migration_revision"] = db.scalar(text("SELECT version_num FROM alembic_version"))
        result["sources"] = db.scalar(select(func.count()).select_from(Source).where(Source.status == "indexed"))
        result["passages"] = db.scalar(select(func.count()).select_from(Passage))
        chunks = list(db.scalars(select(Chunk)))
        result["chunks"] = len(chunks)
        for c in chunks:
            expected = str(
                uuid.uuid5(uuid.NAMESPACE_URL, f"{c.parent_id}:{c.start}:{c.end}:{checksum(c.quote_text.encode())}")
            )
            assert c.id == expected, "Non-deterministic chunk ID"
            p = db.get(Passage, c.parent_id)
            assert p and p.quote_text[c.start : c.end] == c.quote_text
        by_id = {c.id: c for c in chunks}
        store = VectorStore()
        try:
            vector = Embeddings().embed(["Check source-grounded philosophical reflection."])[0]
            store.ensure(len(vector))
            collection = store.client.get_collection(store.collection)
            result["qdrant"] = {
                "collection": store.collection,
                "dimensions": collection.config.params.vectors.size,
                "distance": str(collection.config.params.vectors.distance),
                "points": collection.points_count,
                "payload_indexes": sorted(collection.payload_schema),
            }
            assert collection.points_count == len(chunks), "SQL/vector count mismatch"
            if settings.qdrant_url:
                assert {"author", "work", "document_id", "parent_id", "corpus_version"} <= set(
                    collection.payload_schema
                )
            offset = None
            seen = set()
            while True:
                points, offset = store.client.scroll(
                    store.collection, limit=100, offset=offset, with_payload=True, with_vectors=False
                )
                for point in points:
                    cid = str(point.id)
                    assert cid in by_id and cid not in seen, "Unknown or duplicate vector point"
                    c = by_id[cid]
                    assert point.payload["parent_id"] == c.parent_id
                    assert point.payload["quote_text"] == c.quote_text
                    assert point.payload["text_hash"] == checksum(c.quote_text.encode())
                    assert point.payload["corpus_version"] == settings.corpus_version
                    seen.add(cid)
                if offset is None:
                    break
            assert seen == set(by_id)
            result["retrieval"] = {}
            for mode in ("dense", "hybrid"):
                hits, debug = retrieve(db, store, SCENARIO, mode=mode, rerank=False)
                assert hits and all(verify_quote(h["quote_text"], h["surrounding_passage"]) for h in hits)
                result["retrieval"][mode] = {"passage_ids": [h["passage_id"] for h in hits], "debug": debug}
            result["status"] = "passed"
        finally:
            store.close()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-local-substitutes", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(not args.allow_local_substitutes)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
