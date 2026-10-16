# Portainer no Servidor Pessoal

O destino do stack é o **Servidor Pessoal** (o mesmo host também chamado **Notebook Servidor**), via Portainer. Este repositório deixa o Compose e o script de configuração de fábrica prontos no Git. Subir a stack no Portainer fica para um pedido explícito.

## Pré-requisitos no host

- Docker Engine e Docker Compose v2
- `python3` no host, para `scripts/configurar-fabrica.sh` (só a biblioteca padrão)
- Um único filesystem para `DATA_ROOT` (hardlinks entre torrent e biblioteca)

Confira o usuário dono dos volumes:

```bash
id -u
id -g
```

Use esses números em `PUID` e `PGID`.

## Variáveis (sem gravar segredo no repositório)

Copie os nomes de `.env.example` para **Stacks -> Environment variables**. Não commite o `.env`.

| Variável | O que preencher no Portainer |
|----------|------------------------------|
| `PUID` / `PGID` | `id -u` e `id -g` do Servidor Pessoal |
| `TZ` | Fuso, por exemplo `America/Sao_Paulo` |
| `CONFIG_ROOT` | Caminho absoluto das configs |
| `DATA_ROOT` | Caminho absoluto de torrents e biblioteca, no mesmo disco |
| `PLEX_CLAIM` | Token de [plex.tv/claim](https://plex.tv/claim); expira em minutos e não entra no Git |
| `QBITTORRENT_PASSWORD` | Senha do WebUI. Na primeira subida a imagem linuxserver imprime a senha no log |
| `HOMEPAGE_ALLOWED_HOSTS` | Hosts reais do dashboard, além de localhost |

A senha inicial do qBittorrent sai assim, no host:

```bash
docker compose logs qbittorrent | grep -i password
```

Copie o valor para a variável do stack e recrie o serviço se precisar. Não cole a senha em issue, commit ou README.

## Paths

Exemplos no disco do Servidor Pessoal (ajuste o ponto de montagem real):

```env
CONFIG_ROOT=/mnt/servarr/config
DATA_ROOT=/mnt/servarr/data
```

`DATA_ROOT` e `CONFIG_ROOT` não podem ficar em filesystems diferentes quando houver hardlink entre `/data/torrents` e `/data/media`. Rode uma vez, por SSH:

```bash
bash scripts/init-dirs.sh
```

## Opção A — stack a partir do Git

1. No Portainer: **Stacks** -> **Add stack** -> **Repository**
2. URL: `https://github.com/tiagoassun/servarr-stack`
3. Compose path: `docker-compose.yml`
4. Branch de homologação: `hml`, depois que um humano promover `dev` -> `hml`. A integração dos Agents fica em `dev`. A linha estável é `main`, também só com promoção humana
5. Preencha as variáveis da tabela acima
6. Não marque deploy automático nem webhook GitOps neste ciclo

## Opção B — compose no host

1. Clone o repositório no Servidor Pessoal
2. `cp .env.example .env` e edite só nesse arquivo local
3. No Portainer, use o `docker-compose.yml` local apontando para esse `.env`

## Depois que os containers subirem

Espere Prowlarr, qBittorrent e FlareSolverr responderem.

```bash
docker compose ps
export QBITTORRENT_PASSWORD='...'   # valor lido no log, não versionado
bash scripts/configurar-fabrica.sh
```

O script cria root folders vazios, aponta o download client para `qbittorrent:8080`, liga hardlink e registra FlareSolverr mais o sync do Prowlarr. Não adiciona filme, série, música ou livro, e não enche a fila do Bazarr. O final do script lista o que ainda é manual (Profilarr, libraries vazias do Plex, Seerr, Wizarr e o restante).

## O que não fazer agora

- Não apontar webhook GitOps para redeploy automático sem pedido
- Não desinstalar o Servarr do Win11
- Não misturar o `DATA_ROOT` da instalação do Win11 com o teste do Portainer sem planejar o corte
- Não commitar `.env`, claim do Plex, senha do qBittorrent ou cookie de indexer
