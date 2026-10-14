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
  seerr
  wizarr
  tautulli
  profilarr
  kometa
  maintainerr
  homepage
)

MEDIA=(movies tv music books xxx)
TORRENTS=(movies tv music books xxx)

echo "CONFIG_ROOT=$CONFIG_ROOT"
echo "DATA_ROOT=$DATA_ROOT"

for app in "${APPS[@]}"; do
  mkdir -p "${CONFIG_ROOT}/${app}"
done

mkdir -p \
  "${CONFIG_ROOT}/tdarr/server" \
  "${CONFIG_ROOT}/tdarr/configs" \
  "${CONFIG_ROOT}/tdarr/logs"

for kind in "${TORRENTS[@]}"; do
  mkdir -p "${DATA_ROOT}/torrents/${kind}"
done

for kind in "${MEDIA[@]}"; do
  mkdir -p "${DATA_ROOT}/media/${kind}"
done

mkdir -p \
  "${DATA_ROOT}/torrents/incomplete" \
  "${DATA_ROOT}/tdarr-temp"

# Seerr roda como UID 1000 (node); Maintainerr tambem espera esse dono no volume
if command -v chown >/dev/null 2>&1; then
  chown -R "${PUID:-1000}:${PGID:-1000}" \
    "${CONFIG_ROOT}/seerr" \
    "${CONFIG_ROOT}/maintainerr" \
    "${CONFIG_ROOT}/profilarr" \
    2>/dev/null || true
fi

# Kometa / Homepage: copia stubs versionados se ainda nao existirem
if [[ ! -f "${CONFIG_ROOT}/kometa/config.yml" && -f config/kometa/config.yml.example ]]; then
  cp config/kometa/config.yml.example "${CONFIG_ROOT}/kometa/config.yml"
  echo "Criado ${CONFIG_ROOT}/kometa/config.yml a partir do exemplo (edite o token do Plex)."
fi

if [[ ! -f "${CONFIG_ROOT}/homepage/services.yaml" && -f config/homepage/services.yaml ]]; then
  cp config/homepage/services.yaml "${CONFIG_ROOT}/homepage/services.yaml"
  echo "Criado ${CONFIG_ROOT}/homepage/services.yaml."
fi

# Bootstrap: defaults versionados ja vivem em config/bootstrap/ (repo)
if [[ -d config/bootstrap ]]; then
  mkdir -p "${CONFIG_ROOT}/bootstrap"
fi

echo "Pastas criadas."
echo "Proximo: cp .env.example .env  &&  docker compose up -d  &&  bash scripts/bootstrap.sh"
