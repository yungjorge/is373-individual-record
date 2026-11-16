# Qdrant

Each model/strategy has a deterministic collection using cosine distance. An embedding probe derives the dimension; conflicting dimensions fail instead of silently recreating data. Points have deterministic UUIDv5 IDs based on parent ID, offsets and text hash. Upserts are synchronous and retryable.

Payload fields include chunk_id, parent_id, document_id, author, work, title, translator, edition, book_number, chapter_number, section_number, letter_number, quote_text, semantic_topics, source_url, text_hash and corpus_version. Unknown original reference fields remain null. Server collections provision keyword payload indexes on author, work, document_id, parent_id and corpus_version. Embedded Qdrant does not need server payload indexes.

Author and work filters are applied to both dense and lexical candidates. Parent deduplication prevents multiple overlapping child hits from consuming all result slots; near-identical parent text uses a 0.92 5-word shingle Jaccard threshold. Only one approved edition of each work is indexed initially.

BM25 is **not** implicitly enabled in Qdrant. `rank-bm25` provides a separate BM25Okapi lexical index rebuilt from normalized SQL children for each query. RRF combines dense and lexical rankings; `RETRIEVAL_MODE=dense` disables lexical fusion. At this corpus size this implementation prioritizes clarity over latency. Larger deployments should maintain a revision-keyed BM25 cache or PostgreSQL lexical index and replace text deduplication with persistent fingerprints.

Native embedded storage lives in `backend/data/qdrant-<client release line>` (currently `qdrant-1.15`); only one process can open it. The older `backend/data/qdrant` store is preserved. A versioned directory avoids loading incompatible newer local metadata after pinning the client to the server's 1.15 release line. Compose uses Qdrant server and durable storage. Readiness checks SQL presence, a nonempty collection and dimensions; `python -m app.verify` audits all payloads and parent links against PostgreSQL.
