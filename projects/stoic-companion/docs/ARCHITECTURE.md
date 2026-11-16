# Architecture

The Next.js App Router frontend proxies `/api/v1` to FastAPI. Server secrets stay in Python. The React client consumes server-sent events using fetch so it can attach Auth0 access tokens. A small shadcn-style Radix/CVA Button primitive supports common controls; semantic native elements handle forms and disclosures.

FastAPI verifies Auth0 RS256 signature, expiry, issuer and API audience through cached JWKS. Ownership checks use the verified subject, never a frontend user ID. Conversations, messages, bookmarks, sources, parents, children, ingestion jobs and usage are SQLAlchemy records. Auth0 is optional only in clearly labeled local demo mode. Demo cookies use cryptographically random bearer tokens; only hashes are persisted, with 24-hour expiry.

PostgreSQL is the Compose database; SQLite supports a practical native demo. Alembic supplies an initial migration. Qdrant runs as a server in Compose and as persistent embedded local storage natively. Native Qdrant is single-process; do not open its path from multiple processes. Production deployment should use Qdrant server.

An explicit source registry gates ingestion. Raw snapshot bytes must match the manifest SHA-256 before parsing. Parsers isolate body text and original labels; parents and child offsets remain verbatim after documented newline normalization. Search normalization is stored separately. Deterministic UUIDs and cached embeddings make partial upserts repeatable. Jobs record completion/failure. A changed parser signature fails closed instead of mutating existing citations.

Retrieval is direct Python: contextual query rewrite → embedding → dense Qdrant search + rank-bm25 BM25Okapi → reciprocal rank fusion → optional lexical coverage rerank → parent expansion and near-duplicate rejection. BM25 is rebuilt in memory per request from SQL children; this is transparent and suitable for the small initial corpus, not a large-library search service.

The OpenAI Responses API returns a strict Pydantic Answer. Selected IDs and explanation links must belong to retrieved evidence. Generated prose cannot carry quotation marks or explicit numbered references. The backend attaches exact source chunks, metadata and surrounding parents. No raw provider output is streamed: validated prose is emitted in short SSE deltas, then atomic citation data. This deliberately trades time-to-first-prose for verification before display.

User and assistant messages commit atomically only after validation. Failure emits a sanitized SSE error and saves neither message. One in-flight request per conversation prevents reordering. A process-local rate limiter and spend lock limit the single-worker deployment; a shared reservation service is required before horizontal scaling.

No third-party orchestration framework is needed. The key module boundaries are ingestion, chunking, vectors, retrieval, generation, auth and main/API. Credentials are read from ignored environment configuration. Logs record failure classes rather than prompt text or provider errors.

The Responses integration follows the official [Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses): Python Pydantic schemas are supplied through `responses.parse(text_format=Answer)`, with refusal/incomplete handling. This interface was also checked against the installed SDK signature; credentialed execution is still required.
