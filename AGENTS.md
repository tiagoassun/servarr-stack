# AGENTS.md — servarr-stack

Instruções para agentes neste repositório de código.

## Ordem de leitura (obrigatória)

1. Meta-repo `__Confg-Projetos`: `PRIORIDADE.md` e `WIP.md`.
2. Pasta do projeto: `d:/Docs Locais/Git/__Confg-Projetos/projetos/05-servarr-stack/` — ler `AGENTS.md`, `NEXT-AGENT.md`, `SPEC.md`, `MVP.md`, `ROADMAP.md` (e demais docs conforme a tarefa) **antes** de editar código aqui.
3. Só então este repo (`servarr-stack`); há ponte em `NEXT-AGENT.md` na raiz (brief canônico no meta).

O meta-repo é a fonte de verdade de intenção e escopo.

## Idioma e qualidade

Antes de gravar prosa (README, docs, UI, mensagens):

1. Ler `d:/Docs Locais/Git/__Confg-Projetos/LINGUA-PT-BR.md` e obedecer.
2. Ler `d:/Docs Locais/Git/__Confg-Projetos/FAZER-CERTO-PRIMEIRA-VEZ.md` e obedecer.
## Git flow

```text
feature/<descricao-kebab>  →  hml  →  main
```

- Trabalho novo em `feature/...`.
- Integração / homologação via PR para `hml`.
- Estável via PR `hml` → `main`.
- Conventional commits.
- **Proibido** `workflow_run` disparado a partir de `main` para encadear deploy HML/prod. Deploy HML acompanha a branch `hml`.

## Homologação e produção

- HML e PRD no **mesmo** host: **Servidor Pessoal** / **Notebook Servidor** (nunca só "notebook").
- URLs lab: HML `{slug}-hml.tiagoassun.com.br`; PRD `{slug}.tiagoassun.com.br` (ver `__Confg-Projetos/CONVENCOES.md`).
- Portainer / Compose na LAN; acesso humano preferencial via URL Cloudflare do ambiente.

## Notas do produto

- Backlog (prioridade 5): Docker Compose *Arr + companions (Bazarr, qBittorrent, Plex, Gluetun, Seerr, etc.).
- MVP = stack documentada estável no Servidor Pessoal; config de fábrica com biblioteca vazia.
- Não commitar `.env` real, claim tokens, senhas VPN ou credenciais de indexers.

## Ambiente DEV (Agents Window / Cloud Agent)

- Quando houver `dev`: `feature/*` -> PR -> `dev` (Agents podem abrir/aprovar/mergear). `hml`/`main` só humano.
- Na `feature/*` e no Cloud da missão: editar, testar, commit, push e PR/merge para `dev` **sem** pedir lote a cada passo (brief/pedido da missão já autoriza). Ver `__Confg-Projetos/AGENTS.md`.
- **Proibido** para Agents: merge/push em `hml` ou `main`.
