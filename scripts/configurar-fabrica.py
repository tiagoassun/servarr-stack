#!/usr/bin/env python3
"""Configuração de fábrica do servarr-stack (biblioteca vazia).

Configura *Arr + Prowlarr + Bazarr + categorias qBit via API.
Não adiciona filmes/séries/músicas/livros monitorados.
Não exige dependências além da stdlib.
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
DEFAULTS_PATH = ROOT / "config" / "fabrica" / "defaults.json"


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


SECRET_MARKERS = ("apikey", "api_key", "password", "token", "secret", "cookie")


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if any(marker in str(key).lower() for marker in SECRET_MARKERS):
                cleaned[str(key)] = "<omitido>"
            else:
                cleaned[str(key)] = redact(item)
        return cleaned
    if isinstance(value, list):
        return [redact(item) for item in value[:4]]
    if isinstance(value, str) and len(value) > 240:
        return value[:240]
    return value


def read_api_key_from_yaml_auth(path: Path) -> str | None:
    """Lê só o apikey do bloco auth: no topo. Outros apikey do YAML ficam de fora."""
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None
    in_auth = False
    auth_indent = 0
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if not in_auth:
            if raw.strip() == "auth:":
                in_auth = True
                auth_indent = indent
            continue
        if indent <= auth_indent:
            break
        match = re.match(r"\s*apikey:\s*['\"]?([^'\"#\s]+)", raw)
        if match and match.group(1) not in {"''", '""'}:
            return match.group(1)
    return None


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
        path = config_root() / rel
        if path.suffix.lower() in {".yaml", ".yml"}:
            return read_api_key_from_yaml_auth(path)
        return read_api_key_from_xml(path)
    return None


def resolve_base_url(app: dict[str, Any]) -> str:
    env_name = app.get("baseUrlEnv")
    if env_name and os.environ.get(env_name):
        return os.environ[env_name].rstrip("/")
    # Script no host (Portainer no Servidor Pessoal): preferir localhost + porta publicada
    host_mode = os.environ.get("FABRICA_MODE", "docker").lower()
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
                host = os.environ.get("FABRICA_HOST", "127.0.0.1")
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


def discover_api_prefix(base: str) -> str:
    """apiRoot de /initialize.json. O corpo também traz apiKey; não é impresso."""
    status, body = http_json("GET", f"{base}/initialize.json", timeout=5)
    if status == 200 and isinstance(body, dict):
        root = str(body.get("apiRoot") or "")
        if root.startswith("/api/"):
            return root.rstrip("/") or "/api"
    return ""


def wait_for(url: str, api_key: str | None, seconds: int, interval: int) -> str | None:
    """Devolve o prefixo que respondeu (/api/v3, /api/v1 ou /api)."""
    discovered = discover_api_prefix(url)
    prefixes: list[str] = []
    if discovered:
        prefixes.append(discovered)
    for extra in ("/api/v3", "/api/v1"):
        if extra not in prefixes:
            prefixes.append(extra)
    deadline = time.time() + seconds
    while time.time() < deadline:
        for prefix in prefixes:
            status, _ = http_json(
                "GET",
                f"{url}{prefix}/system/status",
                api_key=api_key,
                timeout=5,
            )
            if status == 200:
                return prefix
        status, _ = http_json("GET", f"{url}/api/system/status", api_key=api_key, timeout=5)
        if status == 200:
            return "/api"
        time.sleep(interval)
    return None


def first_profile_id(base: str, key: str, prefix: str, resources: tuple[str, ...]) -> int | None:
    for resource in resources:
        status, items = http_json("GET", f"{base}{prefix}/{resource}", api_key=key)
        if status != 200 or not isinstance(items, list):
            continue
        standard = 0
        fallback = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                profile_id = int(item.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if profile_id <= 0:
                continue
            if str(item.get("name") or "").lower() == "standard":
                standard = profile_id
                break
            if not fallback:
                fallback = profile_id
        chosen = standard or fallback
        if chosen:
            return chosen
    return None


def ensure_root_folder(base: str, key: str, path: str, prefix: str) -> None:
    status, folders = http_json("GET", f"{base}{prefix}/rootfolder", api_key=key)
    if status != 200:
        print(f"  [aviso] rootfolder GET {status}: {redact(folders)}")
        return
    wanted = path.rstrip("/")
    for folder in folders or []:
        if str(folder.get("path") or "").rstrip("/") == wanted:
            print(f"  root folder ok: {path}")
            return
    status, body = http_json(
        "POST",
        f"{base}{prefix}/rootfolder",
        api_key=key,
        payload={"path": path},
    )
    if status in (200, 201):
        print(f"  root folder criado: {path}")
        return
    # Lidarr e Readarr exigem nome e perfis padrão; Sonarr/Radarr/Whisparr aceitam só o path.
    payload: dict[str, Any] = {"path": path, "name": wanted.rsplit("/", 1)[-1] or "library"}
    quality_id = first_profile_id(base, key, prefix, ("qualityprofile", "qualityProfile"))
    metadata_id = first_profile_id(base, key, prefix, ("metadataprofile", "metadataProfile"))
    if quality_id:
        payload["defaultQualityProfileId"] = quality_id
    if metadata_id:
        payload["defaultMetadataProfileId"] = metadata_id
    status, body = http_json("POST", f"{base}{prefix}/rootfolder", api_key=key, payload=payload)
    if status in (200, 201):
        print(f"  root folder criado: {path}")
    else:
        print(f"  [aviso] rootfolder POST {status}: {redact(body)}")


CATEGORY_FIELDS = {"movieCategory", "tvCategory", "musicCategory", "bookCategory", "category"}


def fill_qbit_fields(
    fields: list[dict[str, Any]],
    qbit: dict[str, Any],
    password: str,
    category: str,
) -> list[dict[str, Any]]:
    filled: list[dict[str, Any]] = []
    for field in fields:
        item = dict(field)
        name = item.get("name")
        if name == "host":
            item["value"] = qbit["host"]
        elif name == "port":
            item["value"] = qbit["port"]
        elif name == "useSsl":
            item["value"] = qbit.get("useSsl", False)
        elif name == "urlBase":
            item["value"] = qbit.get("urlBase", "/")
        elif name == "username":
            item["value"] = qbit.get("username", "admin")
        elif name == "password" and password:
            item["value"] = password
        elif name in CATEGORY_FIELDS:
            item["value"] = category
        filled.append(item)
    return filled


def save_download_client(
    base: str,
    key: str,
    prefix: str,
    payload: dict[str, Any],
    category: str,
    existing_id: int | None,
) -> None:
    if existing_id:
        status, body = http_json(
            "PUT",
            f"{base}{prefix}/downloadclient/{existing_id}",
            api_key=key,
            payload=payload,
            timeout=60,
        )
        action = "atualizado"
    else:
        status, body = http_json(
            "POST",
            f"{base}{prefix}/downloadclient",
            api_key=key,
            payload=payload,
            timeout=60,
        )
        action = "criado"
    if status in (200, 201, 202):
        print(f"  download client qBittorrent {action} (categoria={category})")
        # O POST de criação já testa a conexão. Repetir o teste sem o id novo
        # faz o *Arr recusar o nome como duplicado.
        if not existing_id:
            return
        test_status, test_body = http_json(
            "POST",
            f"{base}{prefix}/downloadclient/test",
            api_key=key,
            payload=payload,
            timeout=60,
        )
        if test_status in (200, 201, 202) and not (isinstance(test_body, list) and test_body):
            print("  download client: teste de conexão ok")
        else:
            print(f"  [aviso] teste do download client {test_status}: {redact(test_body)}")
    else:
        print(f"  [aviso] downloadclient {action} {status}: {redact(body)}")


def ensure_download_client(
    base: str,
    key: str,
    defaults: dict[str, Any],
    category: str,
    prefix: str,
) -> None:
    qbit = defaults["qbittorrent"]
    password = os.environ.get(qbit.get("passwordEnv", "QBITTORRENT_PASSWORD"), "")
    if not password:
        print("  [aviso] QBITTORRENT_PASSWORD vazio; download client não foi alterado")
        return
    status, clients = http_json("GET", f"{base}{prefix}/downloadclient", api_key=key)
    if status != 200:
        print(f"  [aviso] downloadclient GET {status}: {redact(clients)}")
        return
    existing = None
    for client in clients or []:
        if client.get("name") == "qBittorrent" or client.get("implementation") == "QBittorrent":
            existing = client
            break
    if existing:
        # A senha mascarada no GET não dá para comparar. Grava de novo a senha do ambiente.
        payload = dict(existing)
        payload["enable"] = True
        payload["fields"] = fill_qbit_fields(existing.get("fields") or [], qbit, password, category)
        save_download_client(
            base,
            key,
            prefix,
            payload,
            category,
            int(existing.get("id") or 0) or None,
        )
        return
    status, schemas = http_json("GET", f"{base}{prefix}/downloadclient/schema", api_key=key)
    schema = None
    if status == 200:
        for item in schemas or []:
            if item.get("implementation") == "QBittorrent":
                schema = item
                break
    if not schema:
        print("  [aviso] schema QBittorrent não encontrado")
        return
    payload = {
        "enable": True,
        "protocol": "torrent",
        "priority": 1,
        "removeCompletedDownloads": True,
        "removeFailedDownloads": True,
        "name": "qBittorrent",
        "implementation": "QBittorrent",
        "configContract": schema.get("configContract", "QBittorrentSettings"),
        "fields": fill_qbit_fields(schema.get("fields") or [], qbit, password, category),
    }
    save_download_client(base, key, prefix, payload, category, None)


def patch_media_management(base: str, key: str, kind: str, defaults: dict[str, Any], prefix: str) -> None:
    del kind
    mm = dict(defaults.get("mediaManagement") or {})
    status, current = http_json("GET", f"{base}{prefix}/config/mediamanagement", api_key=key)
    if status != 200 or not isinstance(current, dict):
        print(f"  [aviso] mediamanagement GET {status}")
        return
    current.update({k: v for k, v in mm.items() if k in current or k == "copyUsingHardlinks"})
    current["copyUsingHardlinks"] = True
    status, body = http_json(
        "PUT",
        f"{base}{prefix}/config/mediamanagement",
        api_key=key,
        payload=current,
    )
    if status in (200, 202):
        print("  media management: hardlink ligado")
    else:
        print(f"  [aviso] mediamanagement PUT {status}: {redact(body)}")


def configure_arr(name: str, app: dict[str, Any], defaults: dict[str, Any]) -> bool:
    base = resolve_base_url(app)
    key = resolve_api_key(app)
    print(f"\n== {name} ({base}) ==")
    if not key:
        print("  [pulei] sem API key (.env ou config.xml)")
        return False
    prefix = wait_for(base, key, defaults.get("waitSeconds", 180), defaults.get("pollIntervalSeconds", 5))
    if not prefix:
        print("  [pulei] API não respondeu a tempo")
        return False
    print(f"  api: {prefix}")
    ensure_root_folder(base, key, app["rootFolder"], prefix)
    ensure_download_client(base, key, defaults, app["qbitCategory"], prefix)
    patch_media_management(base, key, app.get("kind", ""), defaults, prefix)
    print("  catálogo: intocado (vazio na instalação nova)")
    return True


def configure_prowlarr(defaults: dict[str, Any], keys: dict[str, str]) -> None:
    app = defaults["apps"]["prowlarr"]
    base = resolve_base_url(app)
    key = resolve_api_key(app)
    print(f"\n== prowlarr ({base}) ==")
    if not key:
        print("  [pulei] sem API key")
        return
    prefix = wait_for(base, key, defaults.get("waitSeconds", 180), defaults.get("pollIntervalSeconds", 5))
    if not prefix:
        print("  [pulei] API não respondeu")
        return
    print(f"  api: {prefix}")

    def prowlarr_url(resource: str) -> str:
        return f"{base}{prefix}/{resource}"

    # FlareSolverr indexer proxy
    fl_url = defaults["flaresolverr"]["url"]
    status, proxies = http_json("GET", prowlarr_url("indexerProxy"), api_key=key)
    has_flare = False
    if status == 200:
        for p in proxies or []:
            if p.get("implementation") == "FlareSolverr" or "flare" in (p.get("name") or "").lower():
                has_flare = True
                break
    if not has_flare:
        status, schemas = http_json("GET", prowlarr_url("indexerProxy/schema"), api_key=key)
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
            status, body = http_json("POST", prowlarr_url("indexerProxy"), api_key=key, payload=payload)
            if status in (200, 201):
                print(f"  FlareSolverr proxy: {fl_url}")
            else:
                print(f"  [aviso] indexerProxy POST {status}: {redact(body)}")
        else:
            print("  [aviso] schema FlareSolverr ausente")
    else:
        print("  FlareSolverr proxy já existe")

    # Applications sync
    status, apps_existing = http_json("GET", prowlarr_url("applications"), api_key=key)
    existing_names = {a.get("name") for a in (apps_existing or [])} if status == 200 else set()
    status, schemas = http_json("GET", prowlarr_url("applications/schema"), api_key=key)
    schemas_by_impl = {}
    if status == 200:
        for item in schemas or []:
            schemas_by_impl[item.get("implementation")] = item

    for spec in defaults.get("prowlarrApplications", []):
        if spec["name"] in existing_names:
            print(f"  app sync já existe: {spec['name']}")
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
        status, body = http_json("POST", prowlarr_url("applications"), api_key=key, payload=payload)
        if status in (200, 201):
            print(f"  app sync criado: {spec['name']}")
        else:
            print(f"  [aviso] applications POST {spec['name']} {status}: {redact(body)}")

    print("  indexers: não importados aqui (use backup/UI; ver config/fabrica/)")


def http_form(
    method: str,
    url: str,
    api_key: str,
    fields: dict[str, str],
    timeout: float = 30.0,
) -> tuple[int, Any]:
    data = urllib.parse.urlencode(fields).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Api-Key": api_key,
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return resp.status, body or None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        return exc.code, redact(body)
    except urllib.error.URLError as exc:
        return 0, str(exc.reason if hasattr(exc, "reason") else exc)


def configure_bazarr(defaults: dict[str, Any], keys: dict[str, str]) -> None:
    app = defaults["apps"]["bazarr"]
    base = resolve_base_url(app)
    key = resolve_api_key(app)
    print(f"\n== bazarr ({base}) ==")
    sonarr_key = keys.get("sonarr")
    radarr_key = keys.get("radarr")
    if not key:
        print("  [aviso] sem API key (auth.apikey no config.yaml)")
        return
    if not wait_for(base, key, defaults.get("waitSeconds", 180), defaults.get("pollIntervalSeconds", 5)):
        print("  [pulei] API não respondeu a tempo")
        return
    if not sonarr_key and not radarr_key:
        print("  [pulei] sem keys Sonarr/Radarr")
        return
    # Bazarr 1.x grava settings via form, com chaves settings-<secao>-<campo>.
    # Portas são as internas do Compose, não as publicadas no host.
    fields: dict[str, str] = {}
    if sonarr_key:
        fields.update(
            {
                "settings-general-use_sonarr": "true",
                "settings-sonarr-ip": "sonarr",
                "settings-sonarr-port": "8989",
                "settings-sonarr-base_url": "/",
                "settings-sonarr-ssl": "false",
                "settings-sonarr-apikey": sonarr_key,
            }
        )
    if radarr_key:
        fields.update(
            {
                "settings-general-use_radarr": "true",
                "settings-radarr-ip": "radarr",
                "settings-radarr-port": "7878",
                "settings-radarr-base_url": "/",
                "settings-radarr-ssl": "false",
                "settings-radarr-apikey": radarr_key,
            }
        )
    status, body = http_form("POST", f"{base}/api/system/settings", key, fields)
    if status in (200, 204):
        print("  Sonarr/Radarr ligados (sem itens Wanted de catálogo)")
    else:
        print(f"  [aviso] settings {status}: {redact(body)} - finalize na UI")


def qbit_base_url(defaults: dict[str, Any]) -> str:
    qbit = defaults["qbittorrent"]
    host = os.environ.get("FABRICA_HOST", "127.0.0.1")
    port = os.environ.get("PORT_QBITTORRENT", str(qbit["port"]))
    return f"http://{host}:{port}"


def qbit_session_cookie(headers: Any) -> str | None:
    getter = getattr(headers, "get_all", None)
    values = getter("Set-Cookie") if getter else None
    if not values:
        single = headers.get("Set-Cookie") if hasattr(headers, "get") else None
        values = [single] if single else []
    for item in values:
        pair = str(item).split(";", 1)[0].strip()
        name = pair.split("=", 1)[0]
        if "SID" in name.upper() and "=" in pair:
            return pair
    return None


def qbit_open(
    base: str,
    path: str,
    cookie: str | None,
    data: bytes | None = None,
    content_type: str | None = None,
) -> tuple[int, str, str | None]:
    headers = {"Referer": f"{base}/"}
    if cookie:
        headers["Cookie"] = cookie
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            fresh = qbit_session_cookie(resp.headers) or cookie
            return resp.status, resp.read().decode("utf-8", errors="ignore"), fresh
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="ignore"), cookie
    except urllib.error.URLError as exc:
        return 0, str(exc.reason if hasattr(exc, "reason") else exc), cookie


def prepare_qbittorrent(defaults: dict[str, Any]) -> None:
    print("\n== qbittorrent ==")
    qbit = defaults["qbittorrent"]
    password = os.environ.get(qbit.get("passwordEnv", "QBITTORRENT_PASSWORD"), "")
    base = qbit_base_url(defaults)
    if not password:
        print("  [pulei] QBITTORRENT_PASSWORD vazio - crie categorias na UI ou rode de novo")
        return

    login_data = urllib.parse.urlencode(
        {"username": qbit.get("username", "admin"), "password": password}
    ).encode()
    status, body, cookie = qbit_open(
        base,
        "/api/v2/auth/login",
        None,
        login_data,
        "application/x-www-form-urlencoded",
    )
    if body.strip().lower() == "fails." or not cookie or status not in (200, 204):
        print(f"  [aviso] login qBit HTTP {status}")
        return

    # qBittorrent 5 recusa Host qbittorrent:8080 enquanto a validação de Host/CSRF está ligada.
    prefs = {
        "web_ui_csrf_protection_enabled": False,
        "web_ui_host_header_validation_enabled": False,
    }
    pref_data = urllib.parse.urlencode({"json": json.dumps(prefs)}).encode()
    pref_status, _, cookie = qbit_open(
        base,
        "/api/v2/app/setPreferences",
        cookie,
        pref_data,
        "application/x-www-form-urlencoded",
    )
    if pref_status == 200:
        print("  WebUI: validação de Host e CSRF desligadas para a rede Docker")
    else:
        print(f"  [aviso] setPreferences HTTP {pref_status}")

    list_status, list_body, cookie = qbit_open(base, "/api/v2/torrents/categories", cookie)
    existing: dict[str, Any] = {}
    if list_status == 200:
        try:
            parsed = json.loads(list_body or "{}")
            if isinstance(parsed, dict):
                existing = parsed
        except json.JSONDecodeError:
            existing = {}

    for cat, savepath in qbit.get("categories", {}).items():
        current = existing.get(cat) if isinstance(existing.get(cat), dict) else None
        data = urllib.parse.urlencode({"category": cat, "savePath": savepath}).encode()
        if current is None:
            cat_status, _, cookie = qbit_open(
                base,
                "/api/v2/torrents/createCategory",
                cookie,
                data,
                "application/x-www-form-urlencoded",
            )
            if cat_status == 200:
                print(f"  categoria {cat} -> {savepath}")
            elif cat_status == 409:
                print(f"  categoria {cat} já existe")
            else:
                print(f"  [aviso] categoria {cat}: HTTP {cat_status}")
            continue
        if str(current.get("savePath") or "") == savepath:
            print(f"  categoria {cat} já existe")
            continue
        edit_status, _, cookie = qbit_open(
            base,
            "/api/v2/torrents/editCategory",
            cookie,
            data,
            "application/x-www-form-urlencoded",
        )
        if edit_status == 200:
            print(f"  categoria {cat} -> {savepath}")
        else:
            print(f"  [aviso] categoria {cat} edit HTTP {edit_status}")


def print_checklist(defaults: dict[str, Any]) -> None:
    print("\n== checklist (apps cobertos fora da API automatica) ==")
    for item in defaults.get("checklistManual", []):
        print(f"  - [{item['app']}] {item['acao']}")


def main() -> int:
    load_dotenv(ROOT / ".env")
    if not DEFAULTS_PATH.is_file():
        print(f"defaults não encontrado: {DEFAULTS_PATH}", file=sys.stderr)
        return 1
    defaults = load_defaults()
    print("servarr-stack configurar-fabrica")
    print(f"CONFIG_ROOT={config_root()}")
    print(f"FABRICA_MODE={os.environ.get('FABRICA_MODE', 'docker')}")

    keys: dict[str, str] = {}
    for name in ("sonarr", "radarr", "lidarr", "readarr", "whisparr", "prowlarr", "bazarr"):
        app = defaults["apps"][name]
        k = resolve_api_key(app)
        if k:
            keys[name] = k

    prepare_qbittorrent(defaults)

    for name in ("sonarr", "radarr", "lidarr", "readarr", "whisparr"):
        configure_arr(name, defaults["apps"][name], defaults)

    configure_prowlarr(defaults, keys)
    configure_bazarr(defaults, keys)
    print_checklist(defaults)
    print("\nPronto. Catálogo continua vazio até você adicionar títulos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
