"""Run five isolated indexes; no generated answers are used as relevance ground truth."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def worker(strategy, mode, rerank):
    from sqlalchemy import select

    from .config import ROOT, settings
    from .db import Passage, Session, Usage, init_db
    from .generation import GenerationFailure, assemble, generate, verify_quote
    from .ingestion import ingest, manifest
    from .retrieval import retrieve
    from .vectors import VectorStore

    init_db()
    store = VectorStore()
    try:
        for item in manifest():
            if item["ingestion_status"] == "approved":
                ingest(item, store)
        cases = json.loads((ROOT / "eval/questions.json").read_text(encoding="utf8"))
        with Session() as db:
            available = {pid.split(":part")[0] for pid in db.scalars(select(Passage.id))}
        missing = {pid for case in cases for pid in case["acceptable_passages"] if pid not in available}
        if missing:
            raise ValueError("Benchmark references are absent from the corpus: " + ", ".join(sorted(missing)))
        rows = []
        for case_index, case in enumerate(cases):
            with Session() as db:
                hits, debug = retrieve(db, store, case["question"], mode=mode, rerank=rerank)
            ids = [h["passage_id"].split(":part")[0] for h in hits]
            expected = set(case["acceptable_passages"])
            matches = [i + 1 for i, p in enumerate(ids) if p in expected]
            begin = time.perf_counter()
            requested_provider = settings.generation_provider
            sample_limit = int(os.environ.get("EVAL_GENERATION_SAMPLES", "30"))
            if requested_provider == "openai" and case_index >= sample_limit:
                settings.generation_provider = "demo"
            answer_provider = "demo" if settings.use_demo_generation else "openai"
            failure = None
            usage = {"model": settings.chat_model, "input_tokens": 0, "output_tokens": 0, "estimated_cost": 0.0}
            try:
                answer, usage = generate(case["question"], [], hits)
                result = assemble(answer, hits)
            except GenerationFailure as exc:
                usage = exc.usage
                failure = type(exc).__name__ + ": " + str(exc)
                result = {"citations": []}
            except Exception as exc:
                failure = type(exc).__name__
                result = {"citations": []}
            finally:
                settings.generation_provider = requested_provider
            generation_ms = (time.perf_counter() - begin) * 1000
            rows.append(
                {
                    "id": case["id"],
                    "recall_at_5": len(set(ids) & expected) / len(expected),
                    "mrr": 1 / min(matches) if matches else 0,
                    "retrieval_ms": debug["timing_ms"],
                    "answer_ms": round(generation_ms, 3),
                    "generation_provider": answer_provider,
                    "usage": usage,
                    "generation_error": failure,
                    "citation_validity": not failure
                    and all(c["passage_id"] in {h["passage_id"] for h in hits} for c in result["citations"]),
                    "quote_verification_rate": sum(
                        verify_quote(c["quote_text"], c["surrounding_passage"]) for c in result["citations"]
                    )
                    / len(result["citations"])
                    if result["citations"]
                    else None,
                    "estimated_api_cost_usd": usage["estimated_cost"],
                    "retrieved": ids,
                    "ranking_debug": debug,
                }
            )
        with Session() as db:
            embedding_usage = list(db.scalars(select(Usage).where(Usage.user_id == "system:embeddings")))
        return {
            "strategy": strategy,
            "mode": mode,
            "rerank": rerank,
            "embedding_provider": settings.embedding_provider,
            "embedding_model": "demo-hash-v2" if settings.embedding_provider == "demo" else settings.embedding_model,
            "collection": store.collection,
            "qdrant_mode": "server" if settings.qdrant_url else "embedded",
            "qdrant_server_version": store.client.info().version if settings.qdrant_url else None,
            "source_sql_mode": "isolated SQLite snapshot",
            "embedding_tokens": sum(u.input_tokens for u in embedding_usage),
            "embedding_estimated_cost_usd": sum(u.estimated_cost for u in embedding_usage),
            "rows": rows,
        }
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--strategy", default="structure")
    parser.add_argument("--mode", default="hybrid")
    parser.add_argument("--rerank", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--provider", choices=["demo", "openai"], default="demo")
    parser.add_argument("--generation-provider", choices=["demo", "openai"], default="demo")
    parser.add_argument(
        "--generation-samples",
        type=int,
        default=3,
        help="Real GPT samples per strategy, 0-30; remaining rows use labeled templates.",
    )
    parser.add_argument(
        "--qdrant-url", default="", help="Optional real Qdrant server; evaluation uses a separate collection namespace."
    )
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.worker:
        result = worker(args.strategy, args.mode, args.rerank)
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf8")
        return
    root = Path(__file__).resolve().parents[2]
    from .config import settings

    if not 0 <= args.generation_samples <= 30:
        parser.error("--generation-samples must be between 0 and 30")
    if (args.provider == "openai" or args.generation_provider == "openai") and not settings.openai_api_key:
        parser.error("Configure OPENAI_API_KEY before running a live benchmark")
    output_dir = args.output_dir or root / ("eval/live" if args.provider == "openai" else "eval")
    output_dir.mkdir(parents=True, exist_ok=True)
    shared_cache = (settings.embedding_cache_dir or settings.data_dir / "embeddings").resolve()
    configurations = [
        ("fixed", "dense", False),
        ("recursive", "dense", False),
        ("structure", "dense", False),
        ("structure", "hybrid", False),
        ("structure", "hybrid", True),
    ]
    results = []
    for index, (strategy, mode, rerank) in enumerate(configurations):
        with tempfile.TemporaryDirectory(prefix="stoic-eval-") as temp:
            env = {
                **os.environ,
                "DATA_DIR": temp,
                "DATABASE_URL": "sqlite:///" + str(Path(temp) / "eval.db"),
                "QDRANT_URL": args.qdrant_url,
                "CHUNK_STRATEGY": strategy,
                "DEMO_MODE": "true",
                "EMBEDDING_PROVIDER": args.provider,
                "GENERATION_PROVIDER": args.generation_provider,
                "EMBEDDING_CACHE_DIR": str(shared_cache),
                "EVAL_GENERATION_SAMPLES": str(args.generation_samples),
                "VECTOR_NAMESPACE": "evaluation-v1",
                "OPENAI_API_KEY": settings.openai_api_key,
                "MAX_OUTPUT_TOKENS": str(min(settings.max_output_tokens, 800)),
            }
            output = Path(temp) / "result.json"
            cmd = [
                sys.executable,
                "-m",
                "app.evaluate",
                "--worker",
                "--strategy",
                strategy,
                "--mode",
                mode,
                "--output",
                str(output),
            ] + (["--rerank"] if rerank else [])
            subprocess.run(cmd, env=env, check=True)
            results.append(json.loads(output.read_text()))
            (output_dir / "results.partial.json").write_text(json.dumps(results, indent=2), encoding="utf8")
            print(f"Completed {index + 1}/5: {strategy} {mode} rerank={rerank}", flush=True)
    (output_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf8")
    import statistics

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = ["Fixed + dense", "Recursive + dense", "Structure + dense", "Structure + hybrid", "Hybrid + rerank"]

    def means(key):
        return [statistics.mean(r[key] for r in result["rows"] if r[key] is not None) for result in results]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), layout="constrained")
    x = range(5)
    axes[0].bar([i - 0.17 for i in x], means("recall_at_5"), width=0.34, label="Recall@5", color="#738560")
    axes[0].bar([i + 0.17 for i in x], means("mrr"), width=0.34, label="MRR", color="#b1ba97")
    axes[0].set_ylim(0, 1)
    axes[0].legend()
    axes[1].bar(labels, means("retrieval_ms"), color="#738560")
    axes[1].set_ylabel("Mean retrieval latency (ms)")
    for ax in axes:
        ax.set_xticks(list(x), labels, rotation=22, ha="right")
    fig.suptitle(f"Stoic Companion · {results[0]['embedding_model']} · 30 reference scenarios")
    fig.savefig(output_dir / "retrieval.png", dpi=150)
    report = [
        "# Retrieval evaluation",
        "",
        f"Measured using {results[0]['embedding_model']}, Qdrant {results[0]['qdrant_mode']} cosine search and separate BM25. Source SQL is an isolated SQLite snapshot per strategy, not the application's PostgreSQL database. Generation provider: {args.generation_provider}; up to {args.generation_samples} real GPT samples per strategy when enabled. Remaining rows explicitly use fixed templates.",
        "",
        "All strategies preserve source-unit parents; fixed and recursive baselines change child subdivision within those same parents. This isolates segmentation, but is not a document-wide arbitrary-window baseline. The default target is 280 cl100k tokens. All share the same question set and corpus.",
        "",
        "Reference passages were selected from the actual source sections with explicit editorial rationales in questions.json. They are provisional relevance judgments authored during implementation, not a blinded independent human evaluation. Broader acceptable passages may exist.",
        "",
        "| Strategy | Recall@5 | MRR | Citation validity | Quote verification | Retrieval mean ms | Real GPT mean ms (N) | API cost USD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for i, label in enumerate(labels):
        live_rows = [r for r in results[i]["rows"] if r["generation_provider"] == "openai"]
        live_latency = (
            f"{statistics.mean(r['answer_ms'] for r in live_rows):.2f} ({len(live_rows)})"
            if live_rows
            else "not measured (0)"
        )
        total_cost = results[i]["embedding_estimated_cost_usd"] + sum(
            r["estimated_api_cost_usd"] for r in results[i]["rows"]
        )
        report.append(
            f"| {label} | {means('recall_at_5')[i]:.3f} | {means('mrr')[i]:.3f} | {means('citation_validity')[i]:.3f} | {means('quote_verification_rate')[i]:.3f} | {means('retrieval_ms')[i]:.2f} | {live_latency} | {total_cost:.6f} |"
        )
    report += [
        "",
        "![Measured retrieval comparison](retrieval.png)",
        "",
        "Recall counts unique acceptable parent IDs returned within five, divided by all acceptable IDs. MRR uses the first acceptable hit. Citation and quote rates include the labeled template rows and cover source-card integrity, not prose faithfulness. Per-row provider and usage are recorded in results.json. Cost includes newly requested corpus/query embeddings and generation, at configured price estimates; cache hits cost zero, and shared embedding cache prevents repeat embedding across strategies. Latency includes SQL, Qdrant, lexical indexing and deduplication with warm caches.",
        "",
        "Interpretation: inspect per-question rankings before attributing low scores to chunk sizes. Reference incompleteness, historical vocabulary, query expansion, a lexical reranker and parent-ID coverage can all affect these metrics. Structure is selected for citation boundaries; no strategy is claimed universally superior. No result in this report establishes unmeasured model quality or external human review.",
        "",
        "Reproduce: `python -m app.evaluate` from backend (or set PYTHONPATH=backend). Results JSON includes every query, rank, score and timing. Never compare these numbers to a semantic embedding model without labeling the model difference.",
    ]
    (output_dir / "report.md").write_text("\n".join(report), encoding="utf8")


if __name__ == "__main__":
    main()
