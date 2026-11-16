param([ValidateSet('setup','infra','ingest','api','web','test','lint','evaluate','evaluate-live','migrate','demo-api','demo-ingest')][string]$Task='setup')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONPATH=Join-Path $PSScriptRoot 'backend'
$python=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
switch ($Task) {
 setup { if (!(Test-Path -LiteralPath $python)) { python -m venv .venv }; & $python -m pip install -r backend/requirements.txt; Push-Location frontend; try { npm ci } finally { Pop-Location } }
 infra { $wslScript=(& wsl -d Ubuntu -- wslpath -a (Join-Path $PSScriptRoot 'scripts/wsl-compose.sh')).Trim(); & wsl -d Ubuntu -- bash $wslScript up }
 ingest { & $python -m app.ingestion ingest --all }
 api { & $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 }
 demo-api { $env:DEMO_MODE='true'; $env:GENERATION_PROVIDER='demo'; $env:EMBEDDING_PROVIDER='demo'; $env:CORPUS_VERSION='v1'; & $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 }
 demo-ingest { $env:DEMO_MODE='true'; $env:GENERATION_PROVIDER='demo'; $env:EMBEDDING_PROVIDER='demo'; $env:CORPUS_VERSION='v1'; & $python -m app.ingestion ingest --all }
 web { Push-Location frontend; try { npm run dev } finally { Pop-Location } }
 test { & $python -m pytest -q }
 lint { & $python -m ruff check backend; Push-Location frontend; try { npm run lint } finally { Pop-Location } }
 evaluate { & $python -m app.evaluate }
 evaluate-live { $env:EMBEDDING_CACHE_DIR=Join-Path $PSScriptRoot 'backend/data/live-verification/embeddings'; & $python -m app.evaluate --provider openai --generation-provider openai --generation-samples 3 --qdrant-url http://127.0.0.1:6334 --output-dir eval/live }
 migrate { & $python -m alembic -c backend/alembic.ini upgrade head }
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
