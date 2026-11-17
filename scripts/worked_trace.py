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
        historical = json.loads((APP / "docs/evidence/live-conversation.json").read_text(encoding="utf-8"))
        promotion = db.get(Passage, "enchiridion-long:XXV")
        candidate_id = historical["first"]["debug"]["candidates"][0]["chunk_id"]
        promotion_child = db.get(Chunk, candidate_id)
        citation = next(c for c in historical["first"]["citations"] if c["passage_id"] == promotion.id)
        assert promotion_child is not None and promotion_child.parent_id == promotion.id
        assert promotion_child.quote_text == promotion.quote_text[promotion_child.start:promotion_child.end]
        assert citation["quote_text"] in promotion.quote_text
        assert citation["surrounding_passage"] == promotion.quote_text
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
            "historical_promotion_source_check": {
                "execution": "free source/chunk/quote replay; historical semantic search and generation not rerun",
                "passage_id": promotion.id, "historical_first_candidate_id": candidate_id,
                "offsets": [promotion_child.start, promotion_child.end],
                "chunk_matches_parent_span": True, "saved_quote_matches_approved_parent": True,
                "saved_surrounding_passage_matches_parent": True,
            },
        }
    output = ROOT / "docs/checks/worked-trace.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
finally:
    store.close()
