#!/usr/bin/env bash
# Configuração de fábrica do servarr-stack (biblioteca vazia).
# Uso (no host, após docker compose up -d):
#   bash scripts/configurar-fabrica.sh
#
# Variáveis úteis:
#   FABRICA_MODE=host   (padrão neste script - APIs via localhost:PORT_*)
#   QBITTORRENT_PASSWORD=...
#   SONARR_API_KEY / RADARR_API_KEY / ... (opcional se config.xml já existir)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export FABRICA_MODE="${FABRICA_MODE:-host}"
export FABRICA_HOST="${FABRICA_HOST:-127.0.0.1}"

if ! command -v python3 >/dev/null 2>&1; then
  if ! command -v py >/dev/null 2>&1; then
    echo "python3 não encontrado" >&2
    exit 1
  fi
  exec py -3 "$ROOT/scripts/configurar-fabrica.py"
fi

exec python3 "$ROOT/scripts/configurar-fabrica.py"
