# Infraestrutura de mídia

## Serviços

- Jellyfin: http://127.0.0.1:8096
- qBittorrent: http://127.0.0.1:8080
- Prowlarr: http://127.0.0.1:9696
- Radarr: http://127.0.0.1:7878
- Sonarr: http://127.0.0.1:8989
- Bazarr: http://127.0.0.1:6767
- Jellyseerr: http://127.0.0.1:5055

Use o IP da máquina no lugar de `127.0.0.1` ao acessar de outro dispositivo da rede.

## Ordem de configuração

1. Finalize o usuário administrador e as bibliotecas no Jellyfin.
2. No qBittorrent, confirme a pasta de downloads como `/downloads`.
3. No Radarr, use `/media/Filmes` como raiz de filmes.
4. No Sonarr, use `/media/Series` como raiz de séries.
5. No Radarr e Sonarr, adicione o qBittorrent como download client usando o host `qbittorrent` e a porta `8080`.
6. No Prowlarr, configure apenas indexadores e fontes que você está autorizado a utilizar.
7. No Prowlarr, conecte Radarr e Sonarr pelas URLs internas `http://radarr:7878` e `http://sonarr:8989`.
8. No Bazarr, conecte ao Radarr e Sonarr e escolha os provedores de legendas desejados.
9. No Jellyseerr, conecte ao Jellyfin e ao Radarr/Sonarr para receber pedidos.

## IPTV legal

O Jellyfin já oferece Live TV. Para configurar:

1. Abra Dashboard > Live TV > TV Tuners.
2. Adicione um tuner M3U usando a URL fornecida pelo seu provedor autorizado, ou um arquivo M3U local.
3. Adicione o XMLTV fornecido pelo mesmo provedor para obter o guia de programação.
4. Configure o número máximo de streams conforme seu contrato.

Não incluí listas, credenciais, canais ou serviços de IPTV de terceiros. A aplicação deve usar somente fontes licenciadas ou próprias.

## Comandos

```bash
docker compose -f infra/jellyfin/docker-compose.yml up -d
docker compose -f infra/automation/docker-compose.yml up -d
docker compose -f infra/automation/docker-compose.yml ps
```

Para parar somente a automação:

```bash
docker compose -f infra/automation/docker-compose.yml down
```
