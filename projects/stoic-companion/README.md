# Stoic Companion

A locally runnable philosophical reflection app with traceable public-domain sources, FastAPI, Next.js, PostgreSQL and Qdrant. Every displayed quotation is assembled from stored text and checked against its parent passage. Generated prose is explicitly interpretation.

**Current local runtime:** Ubuntu 24.04 under WSL2, native Docker Engine, PostgreSQL 17, Qdrant 1.15, real `text-embedding-3-small` embeddings and GPT-4.1-mini Responses. Auth0 is optional for this localhost deployment: local guest access is independent of real inference. See [local verification](docs/LOCAL_VERIFICATION.md), [progress](docs/PROGRESS.md), and [measured semantic evaluation](docs/RETRIEVAL_EVALUATION.md).

## Existing WSL installation

From this workspace in Ubuntu:

```bash
bash scripts/wsl-compose.sh up
bash scripts/wsl-compose.sh serve
```

The first command builds/starts the stack; the second follows its logs and keeps a WSL foreground session alive. On this machine native Docker was installed with approval; Docker Desktop and its Windows context remain unchanged. The wrapper explicitly selects Ubuntu's Unix Docker socket. `.env` holds provider settings and `.env.wsl` holds a generated local database password and port choices; both are ignored. Do not print or commit them.

From Windows PowerShell, `./tasks.ps1 infra` invokes the same native Ubuntu launcher.

- Frontend: [localhost:3001](http://localhost:3001)
- API documentation: [localhost:8001/docs](http://localhost:8001/docs)
- Qdrant dashboard: [localhost:6334/dashboard](http://localhost:6334/dashboard)

`bash scripts/wsl-compose.sh status`, `validate`, and `smoke` inspect the existing stack. `serve` leaves containers running when its log stream is interrupted; keep an Ubuntu session alive for native WSL services. The wrapper uses persistent named volumes and loopback-only port bindings. No volumes need to be reset to apply code or key changes.

## Quick start on Windows

Requires Python 3.12+ and Node 20+. From the repository root:

```powershell
./tasks.ps1 setup
./tasks.ps1 demo-ingest
./tasks.ps1 demo-api
# In another terminal:
./tasks.ps1 web
```

Open the Local URL printed by Next.js (normally [localhost:3000](http://localhost:3000)). This works without any external account. Native defaults use SQLite and on-disk Qdrant. Do not run the native API and native ingestion concurrently: Qdrant local mode has an exclusive filesystem lock. Stop the API before reingestion, or use the authenticated admin route. Demo guest sessions persist for 24 hours in the database; they are bearer cookies, not production identities. A guest may send 30 messages, with an additional 12/minute limit.

On Linux/macOS:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
(cd frontend && npm ci)
export PYTHONPATH=backend
python -m app.ingestion ingest --all
uvicorn app.main:app --host 127.0.0.1 --port 8000
# Another terminal: cd frontend && npm run dev
```

## Docker Compose

Copy `.env.example` to `.env`, set your own `POSTGRES_PASSWORD` (URL-safe characters), and start Docker Desktop in Linux container mode:

```sh
docker compose up --build -d
```

This starts PostgreSQL and Qdrant, runs migrations and ingestion, then starts the API and frontend. All exposed ports bind to loopback. The complete stack has been started and verified through native Ubuntu Docker using the WSL wrapper above; the Windows Docker Desktop context is still inactive.

## Live OpenAI + Auth0

For **real inference with local guest access**, set `DEMO_MODE=true`, `GENERATION_PROVIDER=openai`, `EMBEDDING_PROVIDER=openai`, `OPENAI_API_KEY`, and a fresh `CORPUS_VERSION` such as `semantic-v1`. `DEMO_MODE` controls guest authentication; it does not force mocked inference when `GENERATION_PROVIDER=openai`. The health endpoint and UI report the actual generation provider. The verified local configuration uses `RETRIEVAL_MODE=dense` and `RERANK=false`, based on the benchmark, while hybrid remains available.

For Auth0, additionally set `DEMO_MODE=false`, `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `NEXT_PUBLIC_AUTH0_DOMAIN`, `NEXT_PUBLIC_AUTH0_CLIENT_ID`, and `NEXT_PUBLIC_AUTH0_AUDIENCE`. Register a Single Page Application with callback/logout/web origins `http://localhost:3001`, an API audience, and RS256 access tokens. Rebuild the frontend after public Auth0 settings change. Never put the OpenAI key or an Auth0 client secret in browser configuration.

Use a **fresh database/data directory** when switching embedding models or chunking strategies. The collection name isolates model and strategy; SQL ingestion signatures deliberately reject silent changes. Reingest before starting the API. Configure cost estimates and an account-level API spending limit. The local process budget guard is conservative, not a distributed billing system.

## Developer commands

```powershell
./tasks.ps1 test
./tasks.ps1 lint
./tasks.ps1 evaluate
./tasks.ps1 migrate
```

```sh
cd backend
python -m app.ingestion ingest --all
python -m app.ingestion ingest --work meditations
python -m app.ingestion status
python -m app.ingestion validate
python -m app.smoke --live
python -m app.verify
cd ../frontend
npm run lint
npm run build
npx playwright install chromium
npm run test:e2e
npx playwright test --config playwright.live.config.ts
```

Python commands from `backend` require the virtual environment to be active. Root commands can instead set `PYTHONPATH=backend`. Run Playwright with an ingested native database and no other build/dev process writing to `frontend/.next`. The tests start their own servers or reuse healthy local ones. CI uses a fresh source snapshot and executes both desktop and mobile workflows.

Live browser acceptance requires the container stack on port 3001 and makes real billable requests. The normal browser suite explicitly uses offline inference and makes none. `./tasks.ps1 evaluate-live` runs all five semantic retrieval configurations with three GPT samples each and a shared embedding cache; results go to `eval/live`. Its isolated source SQL is SQLite while retrieval uses the real Qdrant server; application PostgreSQL is audited separately. The WSL Compose override shares the same cache with container ingestion to avoid repeat embeddings.

## Reading the implementation

- [Architecture](docs/ARCHITECTURE.md) and [worked RAG example](docs/RAG_EXPLAINED.md)
- [Source rights and editions](docs/SOURCES_AND_LICENSES.md), [manifest](corpus/sources.json)
- [Chunking](docs/CHUNKING.md), [embeddings](docs/EMBEDDINGS.md), [vector database](docs/VECTOR_DATABASE.md)
- [Measured retrieval evaluation](docs/RETRIEVAL_EVALUATION.md), [reference scenarios](eval/questions.json)
- [API](docs/API.md), [deployment](docs/DEPLOYMENT.md), [remaining verification](docs/PROGRESS.md)

Only approved works are indexed. The initial library contains Meditations, Long's Encheiridion and Discourses selections, and Gummere's Letters 1, 13 and 63. The supplied Higginson edition and Shortness of Life candidate remain blocked. Source rights vary outside the US. This is philosophical reflection, not medical care.
