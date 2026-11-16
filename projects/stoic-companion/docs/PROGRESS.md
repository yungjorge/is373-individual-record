# Progress — November 12, 2026

The **real local container application is running and verified**, alongside the preserved offline demo. It uses the existing Ubuntu WSL2 distribution, native Docker Engine, PostgreSQL, Qdrant and OpenAI. Auth0 remains unconfigured; local guest access works with real inference. This is not a declaration of public production readiness.

## Implemented and executed

- Inspected an empty workspace; no Git repository was initialized, so no commits were made.
- Built Next.js App Router / React / TypeScript / Tailwind UI with a Radix/CVA Button, dark/light modes, responsive sidebar, chat, filters, citation reader, bookmarks, source search, copy/retry and history deletion.
- Built FastAPI, Pydantic structured generation, OpenAI Responses adapter, SQLAlchemy persistence, frozen Alembic migration, Auth0 JWT verification, server ownership checks, admin restriction, usage tracking, limits and SSE.
- Indexed six approved registry entries: Casaubon's Meditations, Long's Encheiridion and Discourses selections, Gummere's Letters 1/13/63. The 330 KiB compressed raw snapshots reproduce offline ingestion.
- Ingestion parsed 567 source units and indexed **909 children**. Validation checked every parent/child offset and text hash, plus approved source-file checksums. Repeat ingestion is tested with deterministic point IDs and cached embeddings.
- Ran **52 backend unit/integration tests**, all passing on Windows/Python 3.13 and in the Linux/Python 3.12 application container. Coverage additionally includes independent auth/inference configuration, bounded provider-output repair with usage accounting, complete benchmark reference-ID coverage and interrupted payload-index provisioning.
- Auth verification tests use genuinely signed RSA tokens and reject expiry, audience and signature failures. Live Auth0 browser login was not attempted without configuration.
- Ran **4 offline Playwright tests**, desktop/mobile, plus **1 real-container browser acceptance test**. The latter submitted the requested promotion/jealousy scenario, received real GPT output, checked stored quotations and metadata, expanded original source context and completed a contextual follow-up. Evidence is in `docs/evidence/live-conversation.json` and its screenshots.
- Executed five semantic retrieval configurations on 30 scenarios, with 15 real GPT samples and separately labeled template rows. Fixed/dense recall is 0.450; structure/dense recall 0.433 and MRR 0.415; hybrid and lexical reranking were worse. All 15 latest sampled GPT answers passed final validation. Raw reports are in `eval/live`, corrected offline comparison in `eval/continuation-offline`, and the first semantic run with blocked outputs in `eval/live-before-targeted-repair`. Four missing Seneca reference IDs were corrected without changing source chunks.
- Frontend TypeScript and production builds passed; npm audit found zero vulnerabilities. Windows and container Ruff passed. PostgreSQL migrations actually ran to revision 0001, and the live audit checked all 909 semantic points against SQL, dimensions, indexes, hashes, deterministic IDs and parent offsets. All four long-running services report healthy. See `docs/LOCAL_VERIFICATION.md` for URLs, runtime details, exact scope and reproducible commands.
- Repeated complete live ingestion after deployment: deterministic SQL chunk-ID digest and Qdrant point count stayed identical; zero additional embedding calls were recorded. Original offline data and all existing volumes were preserved.

## External blockers and release work

1. **Docker Desktop issue bypassed safely:** native Ubuntu Docker 29.1.3 and Compose 2.40.3 were installed with approval. Docker Desktop, global WSL configuration, unrelated projects and old volumes were not reset or deleted. The wrapper explicitly uses the native Unix socket. A retained foreground WSL session keeps the local runtime alive.
2. **OpenAI verified:** the supplied key is in ignored `.env` and never printed. Real text-embedding-3-small (1,536 dimensions) and GPT-4.1-mini Responses succeeded. Shared versioned embedding caches avoid repeated corpus charges. The semantic app collection is separate from offline and evaluation collections. The completed latest benchmark's estimated cost was $0.053775, excluding earlier runs/setup and not representing a provider invoice.
3. **Auth0 configuration absent:** provide tenant domain, API audience and SPA client ID and test real callback/logout/JWKS behavior. No credentials were invented.
4. **Rights review:** Higginson's twentieth-century editorial edition and the 1932 Shortness of Life candidate are blocked. Wider Seneca coverage and non-US distribution need separate source/territory review.
5. **Production operations:** current rate/concurrency/spend reservations assume one worker. Add distributed reservations, request idempotency and retention jobs before scaling/public guest access. The crisis keyword detector and prose attribution guard are not comprehensive safety/faithfulness classifiers.
6. **Evaluation scope:** fixed/recursive comparisons share source-unit parents; references need independent human review. Each configuration retrieves all 30 questions but measures real GPT latency on only three to limit cost. Evaluation uses isolated SQLite source snapshots and the real Qdrant server; the actual application PostgreSQL is audited separately. Rates do not prove prose faithfulness.

## Reproduce

The WSL container stack remains running on handoff: frontend 3001, API 8001, Qdrant 6334 and PostgreSQL 5433, all loopback-only. Use `bash scripts/wsl-compose.sh serve` to keep a WSL terminal open, `status` to check health and `validate` for source checks. `./tasks.ps1 demo-ingest` and `demo-api` explicitly select offline providers; normal browser tests do the same. `./tasks.ps1 evaluate-live` reuses the shared embedding cache. The source archive includes notices; secrets/runtime data are ignored.
