import time

from rank_bm25 import BM25Okapi
from sqlalchemy import select

from .config import settings
from .db import Chunk, Passage
from .vectors import Embeddings, expand_query, words


def rrf(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, key in enumerate(ranking, 1):
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
    return scores


def retrieve(db, store, query, author=None, work=None, mode=None, rerank=None, limit=5):
    begin = time.perf_counter()
    mode = mode or settings.retrieval_mode
    rerank = settings.rerank if rerank is None else rerank
    chunks = list(db.scalars(select(Chunk)))
    chunks = [
        c
        for c in chunks
        if (not author or c.metadata_json["author"] == author) and (not work or c.metadata_json["work"] == work)
    ]
    if not chunks:
        return [], {"strategies": [], "timing_ms": 0, "candidates": []}
    by_id = {c.id: c for c in chunks}
    query = expand_query(query)
    vector = Embeddings().embed([query])[0]
    dense = store.search(vector, author, work, 30)
    dense_scores = {str(p.id): p.score for p in dense if str(p.id) in by_id}
    rankings = [list(dense_scores)]
    lexical_scores = {}
    if mode == "hybrid":
        index = BM25Okapi([words(c.search_text) or ["empty"] for c in chunks])
        scores = index.get_scores(words(query))
        lexical_scores = {c.id: float(score) for c, score in zip(chunks, scores, strict=True) if score > 0}
        rankings.append(sorted(lexical_scores, key=lexical_scores.get, reverse=True)[:30])
    fused = rrf(rankings)
    candidates = sorted(fused, key=fused.get, reverse=True)[:30]
    query_words = set(words(query))
    relevance = {
        cid: len(query_words & set(words(by_id[cid].search_text))) / max(1, len(query_words)) for cid in candidates
    }
    final = {cid: fused[cid] + (0.04 * relevance[cid] if rerank else 0) for cid in candidates}
    hits, seen, texts = [], set(), []
    for cid in sorted(candidates, key=final.get, reverse=True):
        c = by_id[cid]
        if c.parent_id in seen:
            continue
        p = db.get(Passage, c.parent_id)
        terms = p.quote_text.lower().split()
        normalized = set(tuple(terms[i : i + 5]) for i in range(max(1, len(terms) - 4)))
        if any(len(normalized & t) / max(1, len(normalized | t)) > 0.92 for t in texts):
            continue
        seen.add(p.id)
        texts.append(normalized)
        hits.append(
            {
                "passage_id": p.id,
                "chunk_id": c.id,
                "quote_text": c.quote_text,
                "surrounding_passage": p.quote_text,
                "metadata": p.metadata_json,
                "dense_score": dense_scores.get(cid),
                "bm25_score": lexical_scores.get(cid),
                "rrf_score": fused[cid],
                "rerank_score": relevance[cid] if rerank else None,
                "score": final[cid],
            }
        )
        if len(hits) >= limit:
            break
    return hits, {
        "expanded_query": query,
        "strategies": ["dense"]
        + (["BM25", "RRF"] if mode == "hybrid" else [])
        + (["lexical-overlap-rerank"] if rerank else []),
        "timing_ms": round((time.perf_counter() - begin) * 1000, 2),
        "candidates": [
            {
                "chunk_id": c,
                "dense_score": dense_scores.get(c),
                "bm25_score": lexical_scores.get(c),
                "rrf_score": fused[c],
                "rerank_score": relevance[c] if rerank else None,
            }
            for c in candidates
        ],
    }
