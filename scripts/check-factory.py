#!/usr/bin/env python3
"""Confere o contrato de fábrica do servarr-stack sem subir containers.

Uso:
  python3 scripts/check-factory.py
  python3 scripts/check-factory.py /tmp/compose.json

O JSON opcional é a saída de `docker compose config --format json`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROOT_FOLDERS = {
    "sonarr": "/data/media/tv",
    "radarr": "/data/media/movies",
    "lidarr": "/data/media/music",
    "readarr": "/data/media/books",
    "whisparr": "/data/media/xxx",
}

CATALOG_ENDPOINTS = (
    "/api/v1/series",
    "/api/v1/movie",
    "/api/v1/artist",
    "/api/v1/book",
    "/api/v1/album",
)

HEALTHY_SERVICES = (
    "prowlarr",
    "qbittorrent",
    "flaresolverr",
    "sonarr",
    "radarr",
    "lidarr",
    "readarr",
    "whisparr",
    "bazarr",
    "seerr",
)

DIRECT_NETWORK_SERVICES = ("qbittorrent", "flaresolverr")


def fail(message: str) -> None:
    print(f"check-factory: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_defaults() -> None:
    defaults = json.loads((ROOT / "config/fabrica/defaults.json").read_text(encoding="utf-8"))
    qbit = defaults["qbittorrent"]
    if qbit.get("host") != "qbittorrent" or qbit.get("port") != 8080:
        fail("qBittorrent precisa apontar para qbittorrent:8080")
    if defaults["mediaManagement"].get("copyUsingHardlinks") is not True:
        fail("hardlink precisa estar ligado em mediaManagement")
    if defaults["flaresolverr"].get("url") != "http://flaresolverr:8191/":
        fail("FlareSolverr precisa usar http://flaresolverr:8191/")
    for name, path in ROOT_FOLDERS.items():
        app = defaults["apps"][name]
        if app.get("rootFolder") != path:
            fail(f"root folder de {name} deveria ser {path}")
        if not app.get("qbitCategory"):
            fail(f"{name} sem categoria do qBittorrent")
    source = (ROOT / "scripts/configurar-fabrica.py").read_text(encoding="utf-8")
    for endpoint in CATALOG_ENDPOINTS:
        if endpoint in source:
            fail(f"configurar-fabrica.py não pode chamar {endpoint}")
    if "gluetun" in source.lower():
        fail("configurar-fabrica.py não deve referenciar Gluetun")


def check_indexers() -> None:
    path = ROOT / "config/fabrica/prowlarr-indexers.example.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    indexers = payload.get("indexers")
    if indexers != []:
        fail("o exemplo versionado de indexers fica vazio; backup real fica fora do Git")


def check_compose(config: dict) -> None:
    services = config.get("services") or {}
    if "gluetun" in services:
        fail("Gluetun foi removido do compose; não deve existir serviço gluetun")
    for name in DIRECT_NETWORK_SERVICES:
        service = services.get(name) or {}
        mode = str(service.get("network_mode") or "")
        if "gluetun" in mode:
            fail(f"{name} não pode usar network_mode do Gluetun")
        networks = service.get("networks")
        if not networks:
            fail(f"{name} precisa estar na rede servarr (sem network_mode de outro serviço)")
    for name in HEALTHY_SERVICES:
        service = services.get(name) or {}
        if not service.get("healthcheck"):
            fail(f"{name} precisa de healthcheck")


def main() -> int:
    check_defaults()
    check_indexers()
    if len(sys.argv) > 1:
        config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        check_compose(config)
    print("check-factory: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
