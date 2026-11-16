#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
action="${1:-status}"
# Ubuntu's minimal engine package does not include Buildx. Use the engine's
# built-in builder without changing any machine-wide Docker configuration.
export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-0}"
runtime_env=.env.wsl
project=stoic-companion-wsl

# Explicit socket/context selection avoids the broken Desktop context and never
# changes the user's global Docker context. No package installation occurs here.
docker_cmd=(/usr/bin/docker --host unix:///var/run/docker.sock)
if ! "${docker_cmd[@]}" info --format '{{.ServerVersion}}' >/dev/null 2>&1; then
  printf '%s\n' 'Native Ubuntu Docker is not available. Approve/install/start the runtime before using this launcher.' >&2
  exit 2
fi

if [[ ( "$action" == up || "$action" == infra ) && ! -f "$runtime_env" ]]; then
  umask 077
  python3 - <<'PY'
from pathlib import Path
import secrets
Path('.env.wsl').write_text('POSTGRES_PASSWORD='+secrets.token_urlsafe(32)+'\nFRONTEND_PORT=3001\nBACKEND_PORT=8001\nPOSTGRES_PORT=5433\nQDRANT_PORT=6334\n')
PY
fi
if [[ ! -f "$runtime_env" ]]; then
  printf '%s\n' 'Run this launcher with up first to create project-local runtime configuration.' >&2
  exit 2
fi
mkdir -p backend/data/live-verification/embeddings
compose=("${docker_cmd[@]}" compose -f compose.yaml -f compose.wsl.yaml -p "$project")
[[ ! -f .env ]] || compose+=(--env-file .env)
compose+=(--env-file "$runtime_env")
case "$action" in
  infra) "${compose[@]}" config --quiet; "${compose[@]}" up -d postgres qdrant ;;
  up) "${compose[@]}" config --quiet; "${compose[@]}" up --build -d ;;
  serve) "${compose[@]}" up -d; "${compose[@]}" logs --follow --tail=5 backend frontend ;;
  status) "${compose[@]}" ps --all ;;
  logs) "${compose[@]}" logs --tail=60 backend frontend ;;
  smoke) "${compose[@]}" exec -T backend python -m app.smoke --live ;;
  validate) "${compose[@]}" exec -T backend python -m app.ingestion validate ;;
  evaluate) "${compose[@]}" exec -T backend python -m app.evaluate --provider openai --generation-provider openai --generation-samples 3 --qdrant-url http://qdrant:6333 --output-dir /workspace/backend/data/eval-live ;;
  *) printf '%s\n' 'Usage: bash scripts/wsl-compose.sh {infra|up|status|logs|smoke|validate|evaluate}' >&2; exit 2 ;;
esac
