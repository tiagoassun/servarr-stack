# servarr-stack

Docker Compose para o ecossistema [Servarr](https://wiki.servarr.com/) (*Arr) e companions: [Bazarr](https://www.bazarr.media/), FlareSolverr, qBittorrent, Plex, [Gluetun](https://github.com/qdm12/gluetun), [Seerr](https://seerr.dev/), [Wizarr](https://github.com/wizarrrr/wizarr), Tautulli, Profilarr, Unpackerr, Kometa, Tdarr, Maintainerr e Homepage.

Objetivo de instalação: **configuração de fábrica** (wiring + indexers quando importados) com **biblioteca vazia** - nenhum filme, série, música ou livro monitorado; nada na fila do Bazarr. Mídia e catálogo entram depois, no uso.

Destino previsto: notebook servidor com **Portainer** (ver [docs/PORTAINER.md](docs/PORTAINER.md)). Ainda não é obrigatório subir lá.

## Serviços

| Serviço | Função | Porta | Hostname |
|---------|--------|-------|----------|
| [Gluetun](https://github.com/qdm12/gluetun) | VPN (kill switch) | - | `gluetun` |
| [Prowlarr](https://wiki.servarr.com/prowlarr) | Indexers | 9696 | `prowlarr` |
| [Sonarr](https://wiki.servarr.com/sonarr) | Séries | 8989 | `sonarr` |
| [Radarr](https://wiki.servarr.com/radarr) | Filmes | 7878 | `radarr` |
| [Lidarr](https://wiki.servarr.com/lidarr) | Música | 8686 | `lidarr` |
| [Readarr](https://wiki.servarr.com/readarr) | Livros (`develop`) | 8787 | `readarr` |
| [Whisparr](https://wiki.servarr.com/whisparr) | Adulto (hotio) | 6969 | `whisparr` |
| [Bazarr](https://www.bazarr.media/) | Legendas | 6767 | `bazarr` |
| [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) | Cloudflare (via VPN) | 8191 | via `gluetun` |
| [qBittorrent](https://www.qbittorrent.org/) | Torrents (via VPN) | 8080 | via `gluetun` |
| [Unpackerr](https://github.com/Unpackerr/unpackerr) | Extrai `.rar`/`.zip` | - | `unpackerr` |
| [Plex](https://www.plex.tv/) | Media server | 32400 | `plex` |
| [Seerr](https://seerr.dev/) | Pedidos de mídia | 5055 | `seerr` |
| [Wizarr](https://github.com/wizarrrr/wizarr) | Convites / onboarding | 5690 | `wizarr` |
| [Tautulli](https://tautulli.com/) | Métricas do Plex | 8181 | `tautulli` |
| [Profilarr](https://github.com/Dictionarry-Hub/profilarr) | Sync TRaSH profiles | 6868 | `profilarr` |
| [Kometa](https://kometa.wiki/) | Coleções / overlays Plex | - | `kometa` |
| [Tdarr](https://tdarr.io/) | Transcode | 8265 / 8266 | `tdarr` |
| [Maintainerr](https://maintainerr.info/) | Limpeza de biblioteca | 6246 | `maintainerr` |
| [Homepage](https://gethomepage.dev/) | Dashboard | 3000 | `homepage` |

qBittorrent e FlareSolverr usam `network_mode: service:gluetun`. Nos outros apps, use o host **`gluetun`** (não `qbittorrent` / `flaresolverr`).

Alternativas deixadas de fora de propósito: Recyclarr (Profilarr cobre), Homarr (Homepage cobre), Deleterr (Maintainerr cobre), Ombi/Petio/Jackett/Autobrr/Cross-Seed/Requestrr.

## Pré-requisitos

- Docker Engine + Docker Compose v2 (ou Portainer com Compose)
- Disco único (mesmo filesystem) para `DATA_ROOT` - hardlinks
- Conta VPN suportada pelo Gluetun ([wiki](https://github.com/qdm12/gluetun-wiki))
- `/dev/net/tun` no host
- `python3` no host para o bootstrap

## Subir o stack

```bash
cp .env.example .env
# Ajuste PUID/PGID/TZ, VPN, paths, HOMEPAGE_ALLOWED_HOSTS

id -u && id -g

bash scripts/init-dirs.sh
docker compose up -d
```

Sem VPN válida o Gluetun não fica healthy e o download client não sobe.

qBittorrent (linuxserver): usuario `admin`; senha no log (copie para `QBITTORRENT_PASSWORD` no `.env`):

```bash
docker compose logs qbittorrent | grep -i password
```

Plex: claim em [plex.tv/claim](https://plex.tv/claim) -> `PLEX_CLAIM` no `.env` (expira em minutos).

## Bootstrap (config de fábrica)

Depois que os containers estiverem healthy:

```bash
# opcional: export QBITTORRENT_PASSWORD='...'
bash scripts/bootstrap.sh
```

O script (`scripts/bootstrap.py` + `config/bootstrap/defaults.json`):

- Cria root folders vazios nos *Arr (`/data/media/...`)
- Cadastra qBittorrent (host `gluetun`) e categorias
- Liga hardlink
- Registra FlareSolverr no Prowlarr e sync Prowlarr -> *Arr
- Tenta ligar Bazarr a Sonarr/Radarr **sem** popular Wanted de catálogo antigo
- Imprime checklist do que falta na UI (Profilarr, Plex libraries vazias, Seerr, Wizarr, etc.)

**Nao** adiciona títulos monitorados. Indexers com secrets: importe backup local (`config/bootstrap/prowlarr-indexers.example.json` como modelo) - não versionar cookies/API keys.

Detalhes: [config/bootstrap/README.md](config/bootstrap/README.md).

## Portainer

Quando for a hora no notebook servidor: [docs/PORTAINER.md](docs/PORTAINER.md).

Resumo: Stack a partir do Git (`docker-compose.yml` + env vars do `.env.example`), paths absolutos em `CONFIG_ROOT` / `DATA_ROOT`, depois `bootstrap.sh` no host.

## VPN (Gluetun)

Exemplo Mullvad (WireGuard) - [docs](https://github.com/qdm12/gluetun-wiki/blob/main/setup/providers/mullvad.md):

```env
VPN_SERVICE_PROVIDER=mullvad
VPN_TYPE=wireguard
WIREGUARD_PRIVATE_KEY=...
WIREGUARD_ADDRESSES=10.x.x.x/32
SERVER_COUNTRIES=Netherlands
```

```bash
docker compose ps gluetun
docker compose logs -f gluetun
```

## Estrutura de pastas (TRaSH)

```text
data/
  torrents/{incomplete,movies,tv,music,books,xxx}/
  media/{movies,tv,music,books,xxx}/
  tdarr-temp/
config/
  bootstrap/          # defaults versionados do bootstrap
  gluetun/ prowlarr/ sonarr/ radarr/ lidarr/ readarr/ whisparr/
  bazarr/ qbittorrent/ plex/ seerr/ wizarr/ tautulli/ profilarr/
  kometa/ tdarr/ maintainerr/ homepage/
```

Referência: [TRaSH - File and Folder Structure](https://trash-guides.info/File-and-Folder-Structure/).

## Como linkar os apps (UI) - referência

O bootstrap cobre a maior parte do wiring. Se precisar na mão:

1. **FlareSolverr** no Prowlarr: `http://gluetun:8191/`
2. **Prowlarr -> Apps**: `http://sonarr:8989`, `http://radarr:7878`, `http://lidarr:8686`, `http://readarr:8787`, `http://whisparr:6969`
3. **Download client** nos *Arr: host `gluetun`, porta `8080`
4. **Categorias qBittorrent**: `tv`/`movies`/`music`/`books`/`xxx` -> `/data/torrents/<cat>`
5. **Root folders**: `/data/media/tv|movies|music|books|xxx` (vazios no início)
6. **Bazarr**: `http://sonarr:8989` e `http://radarr:7878`
7. **Profilarr**: sync TRaSH em Sonarr/Radarr
8. **Seerr / Wizarr / Tautulli / Kometa / Tdarr / Maintainerr / Homepage**: ver checklist do bootstrap

### Unpackerr

Coloque as API keys no `.env` (`SONARR_API_KEY`, etc.) e recrie o container:

```bash
docker compose up -d unpackerr
```

## Diagrama

```text
Wizarr (convite) ----------------> Plex usuários
                                      ^
Seerr (pedidos) --> Sonarr/Radarr ----+
                      |
                 qBittorrent@gluetun (VPN)
                      |
                 Unpackerr (se .rar)
                      |
                 /data/media <--+-- Bazarr
                      |         +-- Tdarr
                      |         +-- Kometa / Maintainerr
                      v
                    Plex <--> Tautulli
                      ^
                 Homepage (atalhos)
Profilarr --> Sonarr/Radarr (TRaSH profiles)
Bootstrap --> wiring *Arr / Prowlarr / qBit / Bazarr
```

## Comandos úteis

```bash
docker compose ps
docker compose logs -f gluetun
docker compose pull && docker compose up -d
bash scripts/bootstrap.sh
docker compose down
```

## Notas

- `DATA_ROOT` em um único filesystem.
- VPN cai = Gluetun corta saida do qBittorrent/FlareSolverr.
- Readarr: tag `develop`. Whisparr: hotio.
- Instalação nova = catálogo vazio; só configuração e (opcionalmente) indexers.
- Lista de tools oficiais: https://wiki.servarr.com/useful-tools
