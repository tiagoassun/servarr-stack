#!/usr/bin/env python3
"""Bootstrap de wiring do servarr-stack (biblioteca vazia).

Configura *Arr + Prowlarr + Bazarr + categorias qBit via API.
Nao adiciona filmes/series/musicas/livros monitorados.
Nao exige dependencias alem da stdlib.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = ROOT / "config" / "bootstrap" / "defaults.json"


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


def load_defaults() -> dict[str, Any]:
    with DEFAULTS_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def config_root() -> Path:
    raw = os.environ.get("CONFIG_ROOT", "./config")
    p = Path(raw)
    if not p.is_absolute():
        p = ROOT / p
    return p


def read_api_key_from_xml(xml_path: Path) -> str | None:
    if not xml_path.is_file():
        return None
    try:
        text = xml_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    m = re.search(r"<ApiKey>([^<]+)</ApiKey>", text)
    if m:
        return m.group(1).strip()
    # Formato Preferences-style
    m = re.search(r'ApiKey="([^"]+)"', text)
    if m:
        return m.group(1).strip()
    try:
        root = ET.fromstring(text)
        for node in root.iter():
            if node.tag.lower().endswith("apikey") and (node.text or "").strip():
                return node.text.strip()
    except ET.ParseError:
        pass
    return None


def resolve_api_key(app: dict[str, Any]) -> str | None:
    env_name = app.get("apiKeyEnv")
    if env_name and os.environ.get(env_name):
        return os.environ[env_name].strip()
    rel = app.get("configXml")
    if rel:
        return read_api_key_from_xml(config_root() / rel)
    return None


def resolve_base_url(app: dict[str, Any]) -> str:
    env_name = app.get("baseUrlEnv")
    if env_name and os.environ.get(env_name):
        return os.environ[env_name].rstrip("/")
    # Bootstrap no host (Portainer notebook): preferir localhost + porta publicada
    host_mode = os.environ.get("BOOTSTRAP_MODE", "docker").lower()
    if host_mode == "host":
        mapping = {
            "sonarr": os.environ.get("PORT_SONARR", "8989"),
            "radarr": os.environ.get("PORT_RADARR", "7878"),
            "lidarr": os.environ.get("PORT_LIDARR", "8686"),
            "readarr": os.environ.get("PORT_READARR", "8787"),
            "whisparr": os.environ.get("PORT_WHISPARR", "6969"),
            "prowlarr": os.environ.get("PORT_PROWLARR", "9696"),
            "bazarr": os.environ.get("PORT_BAZARR", "6767"),
        }
        # Inferir pelo defaultBaseUrl
        default = app.get("defaultBaseUrl", "")
        for name, port in mapping.items():
            if name in default:
                host = os.environ.get("BOOTSTRAP_HOST", "127.0.0.1")
                return f"http://{host}:{port}"
    return app.get("defaultBaseUrl", "").rstrip("/")


def http_json(
    method: str,
    url: str,
    api_key: str | None = None,
    payload: Any = None,
    timeout: float = 30.0,
) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if api_key:
        headers["X-Api-Key"] = api_key
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            if not body:
                return resp.status, None
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        try:
            parsed = json.loads(body) if body else None
        except json.JSONDecodeError:
            parsed = body
        return exc.code, parsed
    except urllib.error.URLError as exc:
        return 0, str(exc.reason if hasattr(exc, "reason") else exc)


def wait_for(url: str, api_key: str | None, seconds: int, interval: int) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        status, _ = http_json("GET", f"{url}/api/v1/system/status", api_key=api_key, timeout=5)
        if status == 200:
            return True
        # Bazarr usa /api/system/status em algumas versoes
        status2, _ = http_json("GET", f"{url}/api/system/status", api_key=api_key, timeout=5)
        if status2 == 200:
            return True
        time.sleep(interval)
    return False


def ensure_root_folder(base: str, key: str, path: str) -> None:
    status, folders = http_json("GET", f"{base}/api/v1/rootfolder", api_key=key)
    if status != 200:
        print(f"  [aviso] rootfolder GET {status}: {folders}")
        return
    existing = {f.get("path") for f in (folders or [])}
    if path in existing:
        print(f"  root folder ok: {path}")
        return
    status, body = http_json("POST", f"{base}/api/v1/rootfolder", api_key=key, payload={"path": path})
    if status in (200, 201):
        print(f"  root folder criado: {path}")
    else:
        print(f"  [aviso] rootfolder POST {status}: {body}")


def ensure_download_client(base: str, key: str, defaults: dict[str, Any], category: str) -> None:
    qbit = defaults["qbittorrent"]
    password = os.environ.get(qbit.get("passwordEnv", "QBITTORRENT_PASSWORD"), "")
    status, clients = http_json("GET", f"{base}/api/v1/downloadclient", api_key=key)
    if status != 200:
        print(f"  [aviso] downloadclient GET {status}: {clients}")
        return
    for client in clients or []:
        if client.get("name") == "qBittorrent" or client.get("implementation") == "QBittorrent":
            print("  download client qBittorrent ja existe")
            return
    # Schema fields via downloadclient/schema
    status, schemas = http_json("GET", f"{base}/api/v1/downloadclient/schema", api_key=key)
    schema = None
    if status == 200:
        for item in schemas or []:
            if item.get("implementation") == "QBittorrent":
                schema = item
                break
    if not schema:
        print("  [aviso] schema QBittorrent nao encontrado")
        return
    fields = []
    for field in schema.get("fields", []):
        name = field.get("name")
        value = field.get("value")
        if name == "host":
            value = qbit["host"]
        elif name == "port":
            value = qbit["port"]
        elif name == "useSsl":
            value = qbit.get("useSsl", False)
        elif name == "urlBase":
            value = qbit.get("urlBase", "/")
        elif name == "username":
            value = qbit.get("username", "admin")
        elif name == "password":
            value = password
        elif name == "movieCategory" or name == "tvCategory" or name == "musicCategory" or name == "bookCategory" or name == "category":
            value = category
        fields.append({**field, "value": value})
    payload = {
        "enable": True,
        "protocol": "torrent",
        "priority": 1,
        "removeCompletedDownloads": True,
        "removeFailedDownloads": True,
        "name": "qBittorrent",
        "implementation": "QBittorrent",
        "configContract": schema.get("configContract", "QBittorrentSettings"),
        "fields": fields,
    }
    status, body = http_json("POST", f"{base}/api/v1/downloadclient", api_key=key, payload=payload)
    if status in (200, 201):
        print(f"  download client qBittorrent criado (categoria={category})")
    else:
        print(f"  [aviso] downloadclient POST {status}: {body}")


def patch_media_management(base: str, key: str, kind: str, defaults: dict[str, Any]) -> None:
    mm = dict(defaults.get("mediaManagement") or {})
    # Endpoint varia: /api/v1/config/mediamanagement
    status, current = http_json("GET", f"{base}/api/v1/config/mediamanagement", api_key=key)
    if status != 200 or not isinstance(current, dict):
        print(f"  [aviso] mediamanagement GET {status}")
        return
    current.update({k: v for k, v in mm.items() if k in current or k == "copyUsingHardlinks"})
    # hardlink
    current["copyUsingHardlinks"] = True
    status, body = http_json("PUT", f"{base}/api/v1/config/mediamanagement", api_key=key, payload=current)
    if status in (200, 202):
        print("  media management: hardlink ligado")
    else:
        print(f"  [aviso] mediamanagement PUT {status}: {body}")


def configure_arr(name: str, app: dict[str, Any], defaults: dict[str, Any]) -> bool:
    base = resolve_base_url(app)
    key = resolve_api_key(app)
    print(f"\n== {name} ({base}) ==")
    if not key:
        print("  [pulei] sem API key (.env ou config.xml)")
        return False
    if not wait_for(base, key, defaults.get("waitSeconds", 180), defaults.get("pollIntervalSeconds", 5)):
        print("  [pulei] API nao respondeu a tempo")
        return False
    ensure_root_folder(base, key, app["rootFolder"])
    ensure_download_client(base, key, defaults, app["qbitCategory"])
    patch_media_management(base, key, app.get("kind", ""), defaults)
    # Garantia: nao importa catalogo - nao chamamos series/movie POST
    print("  catalogo: intocado (vazio na instalacao nova)")
    return True


def configure_prowlarr(defaults: dict[str, Any], keys: dict[str, str]) -> None:
    app = defaults["apps"]["prowlarr"]
    base = resolve_base_url(app)
    key = resolve_api_key(app)
    print(f"\n== prowlarr ({base}) ==")
    if not key:
        print("  [pulei] sem API key")
        return
    if not wait_for(base, key, defaults.get("waitSeconds", 180), defaults.get("pollIntervalSeconds", 5)):
        print("  [pulei] API nao respondeu")
        return

    # FlareSolverr indexer proxy
    fl_url = defaults["flaresolverr"]["url"]
    status, proxies = http_json("GET", f"{base}/api/v1/indexerProxy", api_key=key)
    has_flare = False
    if status == 200:
        for p in proxies or []:
            if p.get("implementation") == "FlareSolverr" or "flare" in (p.get("name") or "").lower():
                has_flare = True
                break
    if not has_flare:
        status, schemas = http_json("GET", f"{base}/api/v1/indexerProxy/schema", api_key=key)
        schema = None
        if status == 200:
            for item in schemas or []:
                if item.get("implementation") == "FlareSolverr":
                    schema = item
                    break
        if schema:
            fields = []
            for field in schema.get("fields", []):
                name = field.get("name")
                value = field.get("value")
                if name == "host":
                    value = fl_url
                fields.append({**field, "value": value})
            payload = {
                "enable": True,
                "name": "FlareSolverr",
                "implementation": "FlareSolverr",
                "configContract": schema.get("configContract", "FlareSolverrSettings"),
                "fields": fields,
                "tags": [],
            }
            status, body = http_json("POST", f"{base}/api/v1/indexerProxy", api_key=key, payload=payload)
            if status in (200, 201):
                print(f"  FlareSolverr proxy: {fl_url}")
            else:
                print(f"  [aviso] indexerProxy POST {status}: {body}")
        else:
            print("  [aviso] schema FlareSolverr ausente")
    else:
        print("  FlareSolverr proxy ja existe")

    # Applications sync
    status, apps_existing = http_json("GET", f"{base}/api/v1/applications", api_key=key)
    existing_names = {a.get("name") for a in (apps_existing or [])} if status == 200 else set()
    status, schemas = http_json("GET", f"{base}/api/v1/applications/schema", api_key=key)
    schemas_by_impl = {}
    if status == 200:
        for item in schemas or []:
            schemas_by_impl[item.get("implementation")] = item

    for spec in defaults.get("prowlarrApplications", []):
        if spec["name"] in existing_names:
            print(f"  app sync ja existe: {spec['name']}")
            continue
        app_key_name = spec["appKey"]
        app_api = keys.get(app_key_name) or resolve_api_key(defaults["apps"].get(app_key_name, {}))
        if not app_api:
            print(f"  [aviso] sem API key para sync {spec['name']}")
            continue
        schema = schemas_by_impl.get(spec["implementation"])
        if not schema:
            print(f"  [aviso] schema ausente: {spec['implementation']}")
            continue
        fields = []
        for field in schema.get("fields", []):
            name = field.get("name")
            value = field.get("value")
            if name == "baseUrl":
                value = spec["baseUrl"]
            elif name == "apiKey":
                value = app_api
            elif name == "prowlarrUrl":
                value = spec.get("prowlarrUrl", base)
            elif name == "syncCategories":
                value = field.get("value")
            fields.append({**field, "value": value})
        payload = {
            "name": spec["name"],
            "syncLevel": spec.get("syncLevel", "fullSync"),
            "implementation": spec["implementation"],
            "configContract": schema.get("configContract"),
            "fields": fields,
            "tags": [],
        }
        status, body = http_json("POST", f"{base}/api/v1/applications", api_key=key, payload=payload)
        if status in (200, 201):
            print(f"  app sync criado: {spec['name']}")
        else:
            print(f"  [aviso] applications POST {spec['name']} {status}: {body}")

    print("  indexers: nao importados aqui (use backup/UI; ver config/bootstrap/)")


def configure_bazarr(defaults: dict[str, Any], keys: dict[str, str]) -> None:
    app = defaults["apps"]["bazarr"]
    base = resolve_base_url(app)
    key = resolve_api_key(app)
    print(f"\n== bazarr ({base}) ==")
    if not key:
        # Bazarr as vezes expoe apikey so apos UI; tentar sem key em settings public
        print("  [aviso] sem API key - configure Sonarr/Radarr na UI se o bootstrap falhar")
    # Tentativa generica de settings (versões variam)
    sonarr_key = keys.get("sonarr")
    radarr_key = keys.get("radarr")
    if not sonarr_key and not radarr_key:
        print("  [pulei] sem keys Sonarr/Radarr")
        return
    # Endpoint comum em Bazarr 1.x
    payload = {
        "sonarr": {
            "ip": "sonarr",
            "port": 8989,
            "base_url": "",
            "ssl": False,
            "apikey": sonarr_key or "",
            "full_update": "Daily",
        },
        "radarr": {
            "ip": "radarr",
            "port": 7878,
            "base_url": "",
            "ssl": False,
            "apikey": radarr_key or "",
            "full_update": "Daily",
        },
    }
    if key:
        status, body = http_json(
            "POST",
            f"{base}/api/system/settings",
            api_key=key,
            payload=payload,
        )
        # Alternativa
        if status not in (200, 204):
            status, body = http_json(
                "PUT",
                f"{base}/api/system/settings",
                api_key=key,
                payload=payload,
            )
        if status in (200, 204):
            print("  Sonarr/Radarr ligados (sem itens Wanted de catalogo)")
        else:
            print(f"  [aviso] settings {status}: {body} - finalize na UI")
    else:
        print("  finalize ligacao Sonarr/Radarr na UI do Bazarr")


def try_qbittorrent_categories(defaults: dict[str, Any]) -> None:
    print("\n== qbittorrent ==")
    qbit = defaults["qbittorrent"]
    password = os.environ.get(qbit.get("passwordEnv", "QBITTORRENT_PASSWORD"), "")
    host_mode = os.environ.get("BOOTSTRAP_MODE", "docker").lower()
    if host_mode == "host":
        host = os.environ.get("BOOTSTRAP_HOST", "127.0.0.1")
        port = os.environ.get("PORT_QBITTORRENT", str(qbit["port"]))
        base = f"http://{host}:{port}"
    else:
        # De dentro da rede Docker o WebUI do qBit responde no gluetun:8080;
        # deste script no HOST use BOOTSTRAP_MODE=host
        host = os.environ.get("BOOTSTRAP_HOST", "127.0.0.1")
        port = os.environ.get("PORT_QBITTORRENT", str(qbit["port"]))
        base = f"http://{host}:{port}"
        print(f"  usando WebUI em {base} (defina QBITTORRENT_PASSWORD)")

    if not password:
        print("  [pulei] QBITTORRENT_PASSWORD vazio - crie categorias na UI ou rode de novo")
        return

    # Login
    login_data = urllib.parse.urlencode(
        {"username": qbit.get("username", "admin"), "password": password}
    ).encode()
    req = urllib.request.Request(
        f"{base}/api/v2/auth/login",
        data=login_data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            cookie = resp.headers.get("Set-Cookie", "")
            body = resp.read().decode()
            if body.strip().lower() != "ok." and "SID=" not in cookie:
                print(f"  [aviso] login qBit: {body!r}")
                return
    except urllib.error.URLError as exc:
        print(f"  [aviso] qBit inacessivel: {exc}")
        return

    sid = None
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith("SID="):
            sid = part
            break
    if not sid:
        print("  [aviso] sem cookie SID")
        return

    for cat, savepath in qbit.get("categories", {}).items():
        data = urllib.parse.urlencode({"category": cat, "savePath": savepath}).encode()
        req = urllib.request.Request(
            f"{base}/api/v2/torrents/createCategory",
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": sid,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                print(f"  categoria {cat} -> {savepath} (HTTP {resp.status})")
        except urllib.error.HTTPError as exc:
            # 409 = ja existe
            if exc.code in (409,):
                print(f"  categoria {cat} ja existe")
            else:
                print(f"  [aviso] categoria {cat}: HTTP {exc.code}")


def print_checklist(defaults: dict[str, Any]) -> None:
    print("\n== checklist (apps cobertos fora da API automatica) ==")
    for item in defaults.get("checklistManual", []):
        print(f"  - [{item['app']}] {item['acao']}")


def main() -> int:
    load_dotenv(ROOT / ".env")
    if not DEFAULTS_PATH.is_file():
        print(f"defaults nao encontrado: {DEFAULTS_PATH}", file=sys.stderr)
        return 1
    defaults = load_defaults()
    print("servarr-stack bootstrap")
    print(f"CONFIG_ROOT={config_root()}")
    print(f"BOOTSTRAP_MODE={os.environ.get('BOOTSTRAP_MODE', 'docker')}")

    keys: dict[str, str] = {}
    for name in ("sonarr", "radarr", "lidarr", "readarr", "whisparr", "prowlarr", "bazarr"):
        app = defaults["apps"][name]
        k = resolve_api_key(app)
        if k:
            keys[name] = k

    for name in ("sonarr", "radarr", "lidarr", "readarr", "whisparr"):
        configure_arr(name, defaults["apps"][name], defaults)

    configure_prowlarr(defaults, keys)
    configure_bazarr(defaults, keys)
    try_qbittorrent_categories(defaults)
    print_checklist(defaults)
    print("\nPronto. Catalogo continua vazio ate voce adicionar titulos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
