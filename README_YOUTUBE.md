# Automação YouTube - ClimaCocal

Sistema de automação para criação diária de transmissões YouTube.

## Instalação

1. Obter credenciais OAuth:
   - https://console.cloud.google.com/apis/credentials
   - Criar OAuth 2.0 Client (Desktop app)
   - Baixar como client_secret.json

2. Setup:
   ```bash
   bash setup.sh
   cp client_secret.json youtube/credentials/
   ```

3. Build e Start:
   ```bash
   docker-compose build
   docker-compose up -d youtube-automation
   ```

4. Autenticação (primeira vez):
   ```bash
   docker exec -it youtube_automation python /youtube/scripts/authenticate.py
   ```

5. Teste:
   ```bash
   docker exec -it youtube_automation python /youtube/scripts/ScriptAutomacao_YT.py
   bash test.sh
   ```

## Monitoramento

- Logs: `tail -f youtube/scripts/logs/*.log`
- Container: `docker logs -f youtube_automation`
- Cron: `docker exec youtube_automation crontab -l`

## Comandos Úteis

- Executar manual: `docker exec -it youtube_automation python /youtube/scripts/ScriptAutomacao_YT.py`
- Reautenticar: `docker exec -it youtube_automation python /youtube/scripts/authenticate.py`
- Restart: `docker-compose restart youtube-automation`