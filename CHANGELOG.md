<!-- CHANGELOG:HEADER:START -->
# CHANGELOG - servarr-stack

Registro diário deste projeto (decisões, código, infra, deploy, testes, bloqueios, docs).

**Antes de editar:** leia `/d/Docs Locais/Git/__Confg-Projetos/skills/CHANGELOG-SKILL.md`.

**Canônico deste repo:** `CHANGELOG.md` (raiz)

**Janela de leitura:** desde o dia 15 do mês anterior até hoje.

**Ordem:** mais recentes no topo.

Tipos: `decisao` | `codigo` | `infra` | `teste` | `deploy` | `docs` | `bloqueio` | `atualizacao`

<!-- CHANGELOG:HEADER:END -->

## 2026-11-17

- `[docs]` Criou a pasta `IA/` com as 15 etapas do ciclo de vida acadêmico e centralizou as etapas em `__Confg-Projetos/IA/` e manteve o diário na raiz deste repo. O `__Confg-Projetos` volta a ser portfólio; detalhe de engenharia fica neste repo.
- `[decisao]` Proibiu chamar o wiring pós-subida de "bootstrap". O nome canônico passou a ser configuração de fábrica: scripts `scripts/configurar-fabrica.sh` e `scripts/configurar-fabrica.py`, pasta `config/fabrica/` (com `defaults.json`), variáveis no estilo `FABRICA_MODE` / `FABRICA_HOST` no lugar de `BOOTSTRAP_*`, e docs/README alinhados a essa nomenclatura.
- `[codigo]` Removeu o serviço Gluetun do `docker-compose.yml`. qBittorrent (portas 8080/6881) e FlareSolverr (8191) passaram a publicar direto na rede Docker `servarr`, com hostnames `qbittorrent` e `flaresolverr` para os *Arr. Motivo: o stack subir sem secrets de provedor VPN. Reintroduzir Gluetun ficou explícito como só sob pedido.
- `[codigo]` Ajustou defaults de fábrica para o mundo sem VPN (`qbittorrent.host` = `qbittorrent`, `flaresolverr.url` = `http://flaresolverr:8191/`), manteve `scripts/check-factory.py` validando o contrato sem Gluetun, e CI em `.github/workflows/ci.yml` checando `configurar-fabrica.sh`, `check-factory.py` e `docker compose config`. No Windows do runner/host, `python3` via stub da Microsoft Store quebrou; o caminho usado foi `py -3`.
- `[deploy]` Com aprovação humana, promoveu o ciclo no GitHub até `main`: no `servarr-stack`, PRs #18 (`feature/remove-gluetun` -> `dev`), #19 (`dev` -> `hml`) e #20 (`hml` -> `main`); no meta `__Confg-Projetos`, PRs #35 -> `dev`, #36 -> `hml`, #37 -> `main`. Depois ainda entrou trabalho adicional em `dev` (ex.: merge #21 de `feature/mvp-stack-bootstrap` e fix de fábrica para API *Arr v3 / qBit 5.1), deixando `origin/dev` à frente de `hml`/`main` em parte do conteúdo.
- `[decisao]` Para Agents Window / Cloud, a branch designada a continuar foi `feature/mvp-stack-bootstrap` (atualizar contra `origin/dev`), não inventar nome novo tipo `feature/cloud-validate-factory`. Humano cobrou: Agents ficam na branch em que já estavam; sem criar branches aleatórias.
- `[pesquisa]` Explicou Homarr: dashboard self-hosted de atalhos/status. No stack atual não entra; o README já marca Homarr como alternativa coberta pelo Homepage ([gethomepage.dev](https://gethomepage.dev/)), serviço `homepage` na porta 3000 com config em `config/homepage/`.
- `[decisao]` Confirmou ficar com Homepage e não acrescentar Homarr. Homarr ganha em UI tipo "app store" / multi-utilizador; Homepage é YAML, leve e já no Compose. Meter os dois só duplica papel.
- `[decisao]` Sobre "tem mais coisas para colocar no stack?": para o MVP, não. O Compose já cobre Prowlarr, Sonarr, Radarr, Lidarr, Readarr, Whisparr, Bazarr, FlareSolverr, qBittorrent, Unpackerr, Plex, Seerr, Wizarr, Tautulli, Profilarr, Kometa, Tdarr, Maintainerr e Homepage. O buraco restante é ops (Portainer no Servidor Pessoal, `configurar-fabrica.sh` de verdade, claim Plex, senha qBit, indexers fora do git, polish de Seerr/Wizarr/Maintainerr/Kometa/Tdarr), não mais container. Alternativas de fora de propósito: Recyclarr, Homarr, Ombi, Petio, Jackett, Deleterr, Autobrr, Cross-Seed, Requestrr; Gluetun só se pedir de volta. Candidatos futuros com critério (não buraco do MVP): VPN, notificação (Gotify/ntfy), backup documentado de volumes.
- `[docs]` Glossário das alternativas fora do stack: Homarr = dashboard (coberto por Homepage); Recyclarr = sync TRaSH via CLI (coberto por Profilarr); Ombi e Petio = pedidos de mídia (cobertos por Seerr); Jackett = meta-indexer (coberto por Prowlarr); Deleterr = limpeza de biblioteca (coberto por Maintainerr); Autobrr = anúncios IRC/API de trackers privados; Cross-Seed = mesmo torrent em outros trackers; Requestrr = bot Discord/Telegram para pedidos (Seerr cobre o fluxo web). Autobrr e Cross-Seed são extras de cena de tracker privado, não requisito do MVP.
- `[decisao]` Marcou o projeto como finalizado. Entrega congelada na linha `dev` (não promover automaticamente para `hml`/`main`). Pasta da ficha no meta com `_` no início para sinalizar finalizado: hoje vive em `__Confg-Projetos/dominios/tech/projetos/_06-servarr-stack` (antes o mapa usava `projetos/06-servarr-stack`; o portfólio em `portfolio/PRIORIDADE.md` e o `README` do meta já apontam ranking 6 finalizado, sem polish sem pedido). WIP/anti-padrão: não retomar servarr-stack nem promover `dev` -> `hml`/`main` sem ordem.
- `[bloqueio]` Lote de commit/push da marcação de finalizado (meta + pontes no repo) foi proposto e ficou pendente de aprovação humana; nesta sessão não houve commit/push desse lote. Trabalho local de rename/docs e pontes `AGENTS`/`NEXT-AGENT` foi feito no fio da conversa; o estado canônico do meta já reflete `_06` e finalizado em `dev`.
- `[docs]` Primeira carga do diário canônico nesta sessão: janela desde 2026-10-15; anti-duplicata manteve a linha já existente sobre a pasta `IA/` / ciclo acadêmico e acrescentou o fio acima (nomenclatura fábrica, Gluetun, promoção Git, Agents na branch certa, Homarr/Homepage, escopo do stack, glossário, finalização `_06`). Sem commit/push do CHANGELOG sem pedido.
