"""Execute a free, isolated trace against the preserved application source."""
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "projects/stoic-companion"
scratch = Path(tempfile.mkdtemp(prefix="is373-trace-"))
os.environ.update(
    DATA_DIR=str(scratch), DATABASE_URL="sqlite:///" + str(scratch / "trace.db"),
    DEMO_MODE="true", EMBEDDING_PROVIDER="demo", GENERATION_PROVIDER="demo",
    QDRANT_URL="", CORPUS_VERSION="v1", VECTOR_NAMESPACE="",
    EMBEDDING_CACHE_DIR=str(scratch / "embeddings"), OPENAI_API_KEY="",
)
sys.path.insert(0, str(APP / "backend"))
from app.db import Chunk, Passage, Session, Source, init_db
from app.ingestion import ingest, manifest, validate
from app.retrieval import retrieve
from app.vectors import VectorStore
from sqlalchemy import select

init_db()
store = VectorStore()
try:
    source = next(s for s in manifest() if s["id"] == "enchiridion-long")
    imported = ingest(source, store)
    with Session() as db:
        passage = db.get(Passage, "enchiridion-long:I")
        child = db.scalars(select(Chunk).where(Chunk.parent_id == passage.id).order_by(Chunk.start)).first()
        record = db.get(Source, passage.source_id)
        hits, debug = retrieve(db, store, "What can I control according to Epictetus?", mode="hybrid", rerank=True)
        result = {
            "execution": "offline demo vectors; no model-generated answer or paid API call",
            "import": imported, "validation": validate(), "source_id": record.id,
            "source_checksum": record.metadata_json["source_checksum"],
            "ingestion_signature": record.checksum, "passage_id": passage.id,
            "chunk_id": child.id, "offsets": [child.start, child.end],
            "supporting_chunk": child.quote_text, "source_metadata": record.metadata_json,
            "retrieved_passage_ids": [h["passage_id"] for h in hits],
            "expected_passage_retrieved": any(h["passage_id"] == passage.id for h in hits),
            "strategies": debug["strategies"],
            "illustrative_interpretation_not_model_output": "Focus on your own judgments and actions, while distinguishing external circumstances.",
        }
    output = ROOT / "docs/checks/worked-trace.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
finally:
    store.close()
