# FONTES DE DADOS - Servarr Stack

| Fonte | Uso | Nota |
| --- | --- | --- |
| Configs *Arr / Plex / Seerr | Volumes Docker + configuração de fábrica | Biblioteca começa vazia |
| Indexers (Prowlarr) | Backup local / UI | Secrets fora do Git |
| Downloads | qBittorrent | Hostname `qbittorrent` na rede `servarr` |
| Mídia | `DATA_ROOT` no host | Hardlinks no mesmo filesystem |

## Secrets (nunca no Git)

| Item | Onde |
| --- | --- |
| Plex claim / senhas | `.env` local / Portainer |
| Cookies / API keys de indexers | Backup local fora do repo |
