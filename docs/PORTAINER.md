# Portainer (notebook servidor) - ainda não é obrigatório subir

Guia para quando for a hora. Este repositório já é um Compose padrão; o Portainer consome o mesmo `docker-compose.yml`.

## Opção A - Stack a partir do Git

1. No Portainer: **Stacks** -> **Add stack** -> **Repository**
2. URL: `https://github.com/tiagoassun/servarr-stack`
3. Compose path: `docker-compose.yml`
4. Branch: use `hml` (homologação) quando o fluxo Git estiver ativo; até lá pode ser `main`
5. Preencha as **Environment variables** com base no `.env.example` (VPN, `PUID`/`PGID`, paths absolutos)
6. **Não** marque deploy automático até você autorizar (agora o momento ainda não chegou)

### Paths no servidor

Exemplos (ajuste ao disco real do notebook):

```env
CONFIG_ROOT=/mnt/servarr/config
DATA_ROOT=/mnt/servarr/data
```

`DATA_ROOT` precisa ser **um** filesystem (hardlinks). Rode `scripts/init-dirs.sh` uma vez no host (SSH) ou crie a árvore manualmente.

## Opção B - Stack com compose colado / upload

1. Clone o repo no host
2. `cp .env.example .env` e edite
3. Portainer: stack com o `docker-compose.yml` local apontando para o `.env`

## Pós-up

```bash
# no host, com as portas publicadas
export QBITTORRENT_PASSWORD='...'   # do log do qBit ou a que você definiu
bash scripts/bootstrap.sh
```

O bootstrap deixa wiring pronto e **catálogo vazio**. Checklist de Profilarr/Plex/Seerr sai no final do script.

## O que não fazer agora

- Não apontar webhook GitOps para redeploy automático sem pedido
- Não desinstalar o Servarr do Win11
- Não misturar o `DATA_ROOT` de produção do Win11 com o teste do Portainer sem planejar cutover
