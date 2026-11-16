# Implementation plan

Build a local-first Next.js / FastAPI application with PostgreSQL and Qdrant in Compose. SQLite plus on-disk Qdrant and deterministic hashed embeddings provide an explicitly labeled, credential-free demo; production uses OpenAI embeddings and Responses, with Auth0 JWT verification.

1. Verify source editions and rights; pin download checksums, preserve raw inputs, parse original headings without inventing references.
2. Build SQL persistence, resumable ingestion, parent/child offsets, embedding cache and dimension checks.
3. Implement BM25 + dense + RRF retrieval, transparent low-cost reranking, strict structured generation and backend-owned quotations.
4. Add authenticated ownership, bounded streaming, bookmarks, catalog, debug/admin restrictions and usage limits.
5. Build responsive accessible chat and library UI.
6. Execute unit/integration/E2E tests, run an honest five-strategy retrieval benchmark, document measured results and external blockers.

Sources that cannot be confidently licensed or parsed are explicitly blocked rather than silently included. Live credentials and Docker daemon availability are checked independently from offline verification.
