# _06 - Servarr Stack

Docker Compose do ecossistema *Arr e companions (Bazarr, qBittorrent, Plex, Seerr, etc.). **Prioridade 6, finalizado.** Entrega congelada na branch `dev`; agents não retomam sem pedido.

| | |
| --- | --- |
| Repo | [tiagoassun/servarr-stack](https://github.com/tiagoassun/servarr-stack) |
| Path local | `/d/Docs Locais/Git/servarr-stack` |
| WIP | Fora de A/B/C. Finalizado: pasta `_06`; não retomar polish sem pedido explícito |
| Linha de entrega | `origin/dev` (sem promoção automática para `hml`/`main`) |

## Em uma frase

Stack *Arr documentada, estável e repetível no Servidor Pessoal, com biblioteca de fábrica vazia.

## Pontos-chave

- qBittorrent e FlareSolverr na rede `servarr` (sem Gluetun neste ciclo).
- Configuração de fábrica (`scripts/configurar-fabrica.sh`) para root folders, download client e defaults.
- Secrets só no host / Portainer.
