# Bootstrap (config de fábrica)

Objetivo: cada instalação nova do `servarr-stack` sobe com **wiring interno** pronto (paths, qBit, Prowlarr <-> *Arr, FlareSolverr, hardlink) e **biblioteca vazia** (nenhum filme/serie/música/livro monitorado; nada na fila do Bazarr).

## O que e versionado aqui

| Arquivo | Papel |
|---------|--------|
| `defaults.json` | Defaults de wiring para o script |
| `prowlarr-indexers.example.json` | Modelo para backup de indexers (sem secrets) |
| `checklist` impresso pelo script | Passos manuais (Profilarr, Plex claim, Seerr, etc.) |

## O que não vai para o Git

- `prowlarr-indexers.json` com credenciais reais
- Volumes runtime em `CONFIG_ROOT` / `DATA_ROOT` (mídia, DBs gerados)
- `.env` com VPN, claim Plex, senhas

## Como rodar (depois do compose up)

```bash
cp .env.example .env   # se ainda não existir
bash scripts/init-dirs.sh
docker compose up -d
# espere Gluetun healthy e UIs responderem
bash scripts/bootstrap.sh
```

O script lê API keys do `.env` ou dos `config.xml` gerados na primeira subida.

## Portainer

No host do Portainer: mesmos passos via console do stack ou one-shot container com este repositório montado. Detalhes no README raiz (seção Portainer).
