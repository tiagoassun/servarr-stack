#!/usr/bin/env bash
# Bootstrap de wiring do servarr-stack (biblioteca vazia).
# Uso (no host, apos docker compose up -d):
#   bash scripts/bootstrap.sh
#
# Variaveis uteis:
#   BOOTSTRAP_MODE=host   (padrao efetivo neste script - APIs via localhost:PORT_*)
#   QBITTORRENT_PASSWORD=...
#   SONARR_API_KEY / RADARR_API_KEY / ... (opcional se config.xml ja existir)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export BOOTSTRAP_MODE="${BOOTSTRAP_MODE:-host}"
export BOOTSTRAP_HOST="${BOOTSTRAP_HOST:-127.0.0.1}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 nao encontrado" >&2
  exit 1
fi

exec python3 "$ROOT/scripts/bootstrap.py"
