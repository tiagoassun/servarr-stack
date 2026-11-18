# SPEC - Servarr Stack

## Problema

Quer-se um homelab *Arr coerente (indexers -> download -> biblioteca -> Plex/pedidos) com instalação repetível no **Servidor Pessoal**, começando vazia e documentada.

## Visão de produto

- Compose único com serviços Servarr + companions
- Config de fábrica (wiring) com biblioteca vazia
- Operação via Portainer no Servidor Pessoal; secrets só em `.env` local / Portainer

## Requisitos funcionais

| ID | Requisito | Horizonte |
| --- | --- | --- |
| RF01 | `docker compose up` sobe o core documentado com healthchecks | MVP |
| RF02 | Configuração de fábrica cria root folders vazios + cadastra download client (`qbittorrent`) | MVP |
| RF03 | Biblioteca vazia: nada na fila; mídia entra só no uso posterior | MVP |
| RF04 | Docs de Portainer / paths no README do repo | MVP |
| RF05 | Acesso humano preferencial via Cloudflare (quando publicado) | ~metade |
| RF06 | Políticas Maintainerr / Kometa / Tdarr alinhadas ao uso real | completo |
| RF07 | Backup documentado de configs e volumes críticos | completo |
| RF08 | VPN opcional (ex.: Gluetun) como fatia futura, sem bloquear Cloud Agents | pós-MVP |

## Requisitos não funcionais

- Disco único para `DATA_ROOT` (hardlinks)
- Secrets (Plex claim, senhas) fora do git
- HML/ops no **Servidor Pessoal** - nunca chamar só de "notebook"
- Fluxo `feature` -> `dev` -> `hml` -> `main`; **proibido** `workflow_run` a partir de `main`
