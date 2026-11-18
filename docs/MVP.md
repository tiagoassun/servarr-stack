# MVP - Servarr Stack

## Fatia

**Stack documentada estável no Servidor Pessoal**: Compose sobe, configuração de fábrica com biblioteca vazia, download client coerente. Não exige biblioteca populada nem polish de todos os companions. Sem VPN embutida (Gluetun) neste ciclo.

## Entregáveis

1. `docker-compose` + `.env.example` cobrindo o conjunto documentado no README
2. `scripts/init-dirs.sh` + `scripts/configurar-fabrica.sh` produzindo config de fábrica vazia
3. qBittorrent e FlareSolverr na rede `servarr` (hostnames `qbittorrent` / `flaresolverr`)
4. Documentação Portainer / pré-requisitos (PUID/PGID, paths)
5. Sem secrets no repositório

## Critérios de aceite

- [ ] Stack sobe no **Servidor Pessoal** (Portainer ou Compose) com serviços core healthy
- [ ] Configuração de fábrica deixa *Arr com root folders vazios e download client apontando para `qbittorrent`
- [ ] Biblioteca/fila vazias após fábrica
- [ ] README cobre claim Plex e senha qBittorrent sem expor secrets
- [ ] CI/docs no fluxo `feature` -> `dev` -> `hml`

## Estimativa

Ops intercalado (lateral). MVP = estabilidade documentada, não "catálogo completo".
