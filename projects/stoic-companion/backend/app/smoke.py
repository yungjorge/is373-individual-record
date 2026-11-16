"""Small, explicit live-provider test; no keys or raw provider exceptions are printed."""

import argparse
import json
import time
from pathlib import Path

from .config import settings
from .db import init_db
from .generation import assemble, generate
from .ingestion import download, manifest, units
from .vectors import Embeddings


def run_live_smoke():
    if not settings.openai_api_key:
        return {
            "status": "blocked",
            "reason": "Configure OPENAI_API_KEY in the project .env; its value is never printed.",
        }
    init_db()
    old = (settings.generation_provider, settings.embedding_provider, settings.max_output_tokens)
    try:
        settings.generation_provider = "openai"
        settings.embedding_provider = "openai"
        settings.max_output_tokens = min(settings.max_output_tokens, 650)
        if settings.embedding_model != "text-embedding-3-small":
            raise ValueError("Smoke test requires text-embedding-3-small")
        start = time.perf_counter()
        vector = Embeddings().embed(["Reflect on what is in our power."])[0]
        embedding_ms = (time.perf_counter() - start) * 1000
        item = next(i for i in manifest() if i["id"] == "enchiridion-long")
        _, text, meta = units(item, download(item))[0]
        evidence = [
            {
                "passage_id": "enchiridion-long:I",
                "quote_text": text,
                "surrounding_passage": text,
                "metadata": {
                    **{k: item[k] for k in ("author", "title", "translator", "edition", "source_url")},
                    **meta,
                },
            }
        ]
        start = time.perf_counter()
        answer, usage = generate(
            "In at most 100 words, help me distinguish my choices from an uncertain outcome. Select only the supplied source and offer one small exercise.",
            [],
            evidence,
        )
        result = assemble(answer, evidence)
        if not result["citations"]:
            raise ValueError("Smoke test returned no verified citation")
        return {
            "status": "passed",
            "embedding_model": settings.embedding_model,
            "embedding_dimensions": len(vector),
            "embedding_ms": round(embedding_ms, 2),
            "generation_ms": round((time.perf_counter() - start) * 1000, 2),
            "usage": usage,
            "verified_citation_ids": answer.selected_passage_ids,
            "result": result,
        }
    except Exception as exc:
        status = getattr(exc, "status_code", None)
        return {
            "status": "failed",
            "error_type": type(exc).__name__,
            "http_status": status,
            "reason": "Live smoke test did not validate. Check provider access/billing, model support and backend logs; no provider error body is exposed.",
        }
    finally:
        settings.generation_provider, settings.embedding_provider, settings.max_output_tokens = old


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        required=True,
        help="Make one embedding and up to two small generation attempts (bounded validation repair; SDK retries apply).",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_live_smoke()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 2)


if __name__ == "__main__":
    main()
