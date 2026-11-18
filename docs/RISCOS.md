# RISCOS - Servarr Stack

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Download sem VPN no lab | Médio | Aceito neste ciclo; VPN opcional pós-MVP |
| Secrets no git (`.env`, claim, indexers) | Alto | Só `.env.example`; Portainer/env local |
| Disco sem hardlinks / paths quebrados | Médio | Um filesystem para `DATA_ROOT`; `init-dirs` |
| Escopo "todos os companions polidos" no MVP | Médio | MVP = stack estável + fábrica vazia |
| Confundir host com "notebook" | Baixo/Docs | Sempre **Servidor Pessoal** / **Notebook Servidor** |
| Competir com Slot A sem ordem | Médio | Backlog 5; não roubar Slot A sem ordem |

## Operação no Servidor Pessoal

- Backup de volumes de config
- Não expor portas cruas como acesso primário (Cloudflare)
- Revisar `HOMEPAGE_ALLOWED_HOSTS` e claims expirados
