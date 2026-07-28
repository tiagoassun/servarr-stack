# servarr-stack

Docker Compose para levantar o ecossistema [Servarr](https://wiki.servarr.com/) (*Arr), mais [Bazarr](https://www.bazarr.media/), FlareSolverr, qBittorrent, Plex e [Gluetun](https://github.com/qdm12/gluetun) - na mesma rede, com pastas compartilhadas para hardlinks e VPN no cliente de download.

## Servicos

| Servico | Funcao | Porta padrao | Hostname na rede |
|---------|--------|--------------|------------------|
| [Gluetun](https://github.com/qdm12/gluetun) | VPN (kill switch) | - | `gluetun` |
| [Prowlarr](https://wiki.servarr.com/prowlarr) | Indexers (sync com os *Arr) | 9696 | `prowlarr` |
| [Sonarr](https://wiki.servarr.com/sonarr) | Series (TV) | 8989 | `sonarr` |
| [Radarr](https://wiki.servarr.com/radarr) | Filmes | 7878 | `radarr` |
| [Lidarr](https://wiki.servarr.com/lidarr) | Musica | 8686 | `lidarr` |
| [Readarr](https://wiki.servarr.com/readarr) | Livros (imagem `develop`) | 8787 | `readarr` |
| [Whisparr](https://wiki.servarr.com/whisparr) | Adulto (imagem hotio) | 6969 | `whisparr` |
| [Bazarr](https://www.bazarr.media/) | Legendas (Sonarr + Radarr) | 6767 | `bazarr` |
| [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) | Bypass Cloudflare (via VPN) | 8191 | via `gluetun` |
| [qBittorrent](https://www.qbittorrent.org/) | Cliente torrent (via VPN) | 8080 | via `gluetun` |
| [Plex](https://www.plex.tv/) | Media server | 32400 | `plex` |

qBittorrent e FlareSolverr usam `network_mode: service:gluetun`. As portas deles sao publicadas no container **Gluetun**. Nos outros apps, o host e `gluetun` (nao `qbittorrent` / `flaresolverr`).

## Pre-requisitos

- Docker Engine + Docker Compose v2
- Disco unico (ou o mesmo filesystem) para `DATA_ROOT` - necessario para hardlinks
- Conta VPN suportada pelo Gluetun ([wiki de providers](https://github.com/qdm12/gluetun-wiki))
- No host: dispositivo `/dev/net/tun` (padrao em Linux; no Docker Desktop costuma ja existir)

## Subir o stack

```bash
cp .env.example .env
# Ajuste PUID/PGID/TZ, credenciais VPN e, se quiser, caminhos e portas

# Linux/macOS: descubra PUID/PGID
id -u
id -g

bash scripts/init-dirs.sh
docker compose up -d
```

Sem `VPN_SERVICE_PROVIDER` (e credenciais validas) o Gluetun nao sobe saudavel e o qBittorrent/FlareSolverr ficam presos nele.

Credencial inicial do qBittorrent (linuxserver): usuario `admin`. A senha e impressa no log na primeira subida:

```bash
docker compose logs qbittorrent | grep -i password
```

WebUI do qBittorrent no host: `http://localhost:8080` (porta publicada pelo Gluetun).

Plex: gere um claim em [plex.tv/claim](https://plex.tv/claim), coloque em `PLEX_CLAIM` no `.env` e suba (ou reinicie) o container em seguida - o token expira em poucos minutos.

## VPN (Gluetun)

Preencha no `.env` conforme o provider. Exemplos:

**Mullvad (WireGuard)** - veja [gluetun-wiki / mullvad](https://github.com/qdm12/gluetun-wiki/blob/main/setup/providers/mullvad.md):

```env
VPN_SERVICE_PROVIDER=mullvad
VPN_TYPE=wireguard
WIREGUARD_PRIVATE_KEY=...
WIREGUARD_ADDRESSES=10.x.x.x/32
SERVER_COUNTRIES=Netherlands
```

**ProtonVPN (OpenVPN ou WireGuard)** - veja a [pagina do provider](https://github.com/qdm12/gluetun-wiki/blob/main/setup/providers/protonvpn.md).

Ajuste `FIREWALL_OUTBOUND_SUBNETS` para a subnet da sua LAN se o WebUI nao abrir da rede local.

Conferir tunel:

```bash
docker compose ps gluetun
docker compose logs -f gluetun
```

## Estrutura de pastas (TRaSH)

Tudo sob `DATA_ROOT` montado como `/data` nos *Arr e no qBittorrent (Bazarr/Plex veem so `/data/media`). Assim o caminho e o mesmo em todos os containers e o import vira hardlink, nao copia.

```text
data/
  torrents/
    incomplete/
    movies/
    tv/
    music/
    books/
    xxx/
  media/
    movies/
    tv/
    music/
    books/
    xxx/
config/
  gluetun/ prowlarr/ sonarr/ radarr/ lidarr/ readarr/ whisparr/
  bazarr/ qbittorrent/ plex/
```

Referencia: [TRaSH - File and Folder Structure](https://trash-guides.info/File-and-Folder-Structure/).

## Como linkar os apps (UI)

Os *Arr se enxergam pelo **nome do servico** na rede `servarr`. qBittorrent e FlareSolverr: use o hostname **`gluetun`**.

### 1. FlareSolverr no Prowlarr

Prowlarr -> Settings -> Indexers -> Indexer Proxies -> Add -> FlareSolverr:

- Tags: ex. `flaresolverr` (associe aos indexers que precisam)
- Host: `http://gluetun:8191/`

### 2. Prowlarr -> *Arr

Prowlarr -> Settings -> Apps -> Add:

| App | Prowlarr Server | Sync URL / Host |
|-----|-----------------|-----------------|
| Sonarr | `http://prowlarr:9696` | `http://sonarr:8989` |
| Radarr | idem | `http://radarr:7878` |
| Lidarr | idem | `http://lidarr:8686` |
| Readarr | idem | `http://readarr:8787` |
| Whisparr | idem | `http://whisparr:6969` |

Use a API key de cada app (Settings -> General).

### 3. qBittorrent nos *Arr

Em Sonarr / Radarr / Lidarr / Readarr / Whisparr -> Settings -> Download Clients -> qBittorrent:

- Host: `gluetun`
- Port: `8080`
- Username / Password: do WebUI

Categorias sugeridas (qBittorrent -> Options -> Downloads -> categorias com save path):

| Categoria | Save path |
|-----------|-----------|
| `tv` | `/data/torrents/tv` |
| `movies` | `/data/torrents/movies` |
| `music` | `/data/torrents/music` |
| `books` | `/data/torrents/books` |
| `xxx` | `/data/torrents/xxx` |

Default save path do qBittorrent: `/data/torrents`. Incomplete: `/data/torrents/incomplete`.

Root folders nos *Arr:

| App | Root folder |
|-----|-------------|
| Sonarr | `/data/media/tv` |
| Radarr | `/data/media/movies` |
| Lidarr | `/data/media/music` |
| Readarr | `/data/media/books` |
| Whisparr | `/data/media/xxx` |

### 4. Bazarr -> Sonarr e Radarr

Bazarr -> Settings -> Sonarr / Radarr:

- Sonarr: `http://sonarr:8989` + API key
- Radarr: `http://radarr:7878` + API key

Path mapping so e necessario se os caminhos diferirem; com este compose, media fica em `/data/media/...` nos tres.

### 5. Plex

Libraries apontando para:

- Movies: `/data/media/movies`
- TV: `/data/media/tv`
- Music: `/data/media/music`
- (opcional) Adulto: `/data/media/xxx`

## Diagrama

```text
Indexers --(FlareSolverr@gluetun/VPN)--> Prowlarr
   --sync--> Sonarr / Radarr / Lidarr / Readarr / Whisparr
                      |
                      v
              qBittorrent@gluetun (VPN)
                 /data/torrents/*
                      |
                hardlink/move
                      v
               /data/media/*
             /        \
        Bazarr        Plex
```

## Comandos uteis

```bash
docker compose ps
docker compose logs -f gluetun
docker compose logs -f sonarr
docker compose pull && docker compose up -d
docker compose down
```

## Notas

- Mantenha `CONFIG_ROOT` e `DATA_ROOT` no mesmo host; `DATA_ROOT` deve ser um unico filesystem.
- Se a VPN cair, o Gluetun corta a saida: qBittorrent e FlareSolverr param de vazar IP real.
- Readarr usa a tag `develop` da imagem linuxserver (branch estavel limitada).
- Whisparr usa imagem [hotio](https://hotio.dev/) (`ghcr.io/hotio/whisparr`).
- Ajuste portas no `.env` se houver conflito no host.
- Guia VPN do Servarr: https://wiki.servarr.com/docker-guide
