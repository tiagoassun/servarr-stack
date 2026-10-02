# AGENTS.md — servarr-stack

Instruções para agentes neste repositório de código.

## Ordem de leitura (obrigatória)

1. Meta-repo `__Confg-Projetos`: `PRIORIDADE.md` e `WIP.md`.
2. Pasta do projeto: `d:/Docs Locais/Git/__Confg-Projetos/projetos/12-servarr-stack/` — ler `AGENTS.md`, `SPEC.md`, `MVP.md`, `ROADMAP.md` (e demais docs conforme a tarefa) **antes** de editar código aqui.
3. Só então este repo (`servarr-stack`).

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

## Homologação

- Stack no **Servidor Pessoal** (também **Notebook Servidor** quando for preciso distinguir do PC do dia a dia).
- **Proibido** chamar esse host só de "notebook".
- Portainer / Compose na LAN do Servidor Pessoal; acesso humano preferencial via URL Cloudflare.

## Notas do produto

- Projeto **lateral** (ops/homelab, fora do ranking 1–10): Docker Compose *Arr + companions (Bazarr, qBittorrent, Plex, Gluetun, Seerr, etc.).
- MVP = stack documentada estável no Servidor Pessoal; config de fábrica com biblioteca vazia.
- Não commitar `.env` real, claim tokens, senhas VPN ou credenciais de indexers.
