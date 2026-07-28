#!/usr/bin/env bash
# Cria a arvore de pastas alinhada ao TRaSH Guides.
# Uso: ./scripts/init-dirs.sh
# Variaveis opcionais: CONFIG_ROOT, DATA_ROOT (padrao: ./config e ./data)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
if [[ -f .env ]]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

CONFIG_ROOT="${CONFIG_ROOT:-./config}"
DATA_ROOT="${DATA_ROOT:-./data}"

APPS=(
  gluetun
  prowlarr
  sonarr
  radarr
  lidarr
  readarr
  whisparr
  bazarr
  qbittorrent
  plex
)

MEDIA=(movies tv music books xxx)
TORRENTS=(movies tv music books xxx)

echo "CONFIG_ROOT=$CONFIG_ROOT"
echo "DATA_ROOT=$DATA_ROOT"

for app in "${APPS[@]}"; do
  mkdir -p "${CONFIG_ROOT}/${app}"
done

for kind in "${TORRENTS[@]}"; do
  mkdir -p "${DATA_ROOT}/torrents/${kind}"
done

for kind in "${MEDIA[@]}"; do
  mkdir -p "${DATA_ROOT}/media/${kind}"
done

mkdir -p "${DATA_ROOT}/torrents/incomplete"

echo "Pastas criadas."
echo "Proximo: cp .env.example .env  &&  docker compose up -d"
