# ClimaCocal - Camera Streaming System

Sistema completo de streaming de câmera IP para YouTube Live com monitoramento, alertas e dashboard web.

## 📋 Visão Geral

O sistema ClimaCocal Camera Streamer permite streaming 24/7 de uma câmera IP diretamente para YouTube Live, com funcionalidades de:

- **Streaming contínuo**: RTSP → YouTube RTMP com reconexão automática
- **Dashboard web**: Interface de monitoramento em tempo real
- **Sistema de alertas**: Notificações via Telegram e email
- **Health checking**: Verificação automatizada de conectividade
- **Fallback inteligente**: Imagem offline quando câmera não disponível
- **Logs detalhados**: Monitoramento completo de atividades

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Câmera IP     │───▶│  Camera Streamer │───▶│  YouTube Live   │
│ (RTSP Stream)   │    │   (FFmpeg)       │    │  (RTMP)         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Web Dashboard   │
                    │   (Flask:8001)   │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │     Alertas      │
                    │ Telegram + Email │
                    └──────────────────┘
```

## 🚀 Instalação Rápida

### 1. Setup Inicial

```bash
# Clone o projeto (se ainda não tiver)
git clone [repository-url]
cd cocalClima

# Execute o setup automático
bash setup_camera.sh
```

### 2. Configuração do .env

Edite o arquivo `.env` e configure as credenciais:

```env
# Configurações da Câmera
CAMERA_RTSP_URL=rtsp://admin:CoraRosa@192.168.69.20:554/cam/realmonitor?channel=1&subtype=0

# YouTube Live
YOUTUBE_STREAM_KEY=yx67-vfxc-q2vb-4rkb-402d
YOUTUBE_RTMP_URL=rtmp://a.rtmp.youtube.com/live2/

# Streaming
STREAM_RESOLUTION=1920x1080
STREAM_FPS=25
STREAM_BITRATE=2500k

# Alertas Telegram (opcional)
TELEGRAM_BOT_TOKEN=seu_bot_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui

# Alertas Email (opcional)  
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app
ALERT_EMAIL=destinatario@gmail.com

# Health Check
HEALTH_CHECK_INTERVAL=30
MAX_RECONNECT_ATTEMPTS=5
RECONNECT_DELAY=10
ENABLE_FALLBACK=true
```

### 3. Build e Start

```bash
# Build do container
docker-compose build camera-streamer

# Iniciar o serviço
docker-compose up -d camera-streamer

# Verificar logs
docker logs -f camera_streamer
```

### 4. Verificação

```bash
# Teste completo do sistema
bash test_camera.sh

# Acessar dashboard
open http://localhost:8001
```

## 📁 Estrutura de Arquivos

```
cocalClima/
├── camera/
│   ├── scripts/
│   │   ├── stream_manager.py      # Gerenciamento do stream FFmpeg
│   │   ├── health_checker.py      # Verificação de saúde da câmera
│   │   ├── alert_service.py       # Sistema de alertas
│   │   ├── dashboard.py           # Dashboard Flask
│   │   ├── utils.py               # Utilitários e configuração
│   │   └── generate_offline_image.py # Gerador de imagem offline
│   ├── templates/
│   │   └── dashboard.html         # Interface web
│   ├── static/
│   │   └── offline.png           # Imagem de fallback (gerada automaticamente)
│   ├── logs/                     # Logs do sistema
│   ├── requirements.txt          # Dependências Python
│   ├── entrypoint.sh            # Script de inicialização
│   └── .gitignore               # Arquivos ignorados
├── Dockerfile.camera            # Container da câmera
├── docker-compose.yml          # Orquestração (atualizado)
├── setup_camera.sh            # Script de setup
├── test_camera.sh             # Script de testes
└── CAMERA_SETUP.md           # Esta documentação
```

## 🔧 Configuração Detalhada

### Variáveis de Ambiente

#### Câmera e Streaming
- `CAMERA_RTSP_URL`: URL RTSP da câmera IP
- `YOUTUBE_STREAM_KEY`: Chave de streaming do YouTube Live
- `YOUTUBE_RTMP_URL`: URL RTMP do YouTube (padrão: rtmp://a.rtmp.youtube.com/live2/)
- `STREAM_RESOLUTION`: Resolução do stream (padrão: 1920x1080)
- `STREAM_FPS`: Taxa de quadros (padrão: 25)
- `STREAM_BITRATE`: Bitrate do vídeo (padrão: 2500k)

#### Health Check
- `HEALTH_CHECK_INTERVAL`: Intervalo entre verificações em segundos (padrão: 30)
- `MAX_RECONNECT_ATTEMPTS`: Tentativas máximas de reconexão (padrão: 5)
- `RECONNECT_DELAY`: Delay entre tentativas em segundos (padrão: 10)
- `ENABLE_FALLBACK`: Habilitar imagem offline quando câmera indisponível (padrão: true)

#### Alertas Telegram
- `TELEGRAM_BOT_TOKEN`: Token do bot Telegram
- `TELEGRAM_CHAT_ID`: ID do chat para receber alertas
- `TELEGRAM_ALERT_COOLDOWN`: Cooldown entre alertas em segundos (padrão: 300)

#### Alertas Email
- `SMTP_HOST`: Servidor SMTP (padrão: smtp.gmail.com)
- `SMTP_PORT`: Porta SMTP (padrão: 587)
- `SMTP_USER`: Usuário do email
- `SMTP_PASSWORD`: Senha do email (recomendado: senha de app)
- `ALERT_EMAIL`: Email de destino para alertas
- `EMAIL_ALERT_COOLDOWN`: Cooldown entre emails em segundos (padrão: 600)

### Configuração de Alertas

#### Telegram Bot Setup
1. Converse com @BotFather no Telegram
2. Crie um novo bot: `/newbot`
3. Copie o token fornecido
4. Adicione o bot ao seu grupo/chat
5. Use @userinfobot para obter o Chat ID

#### Gmail App Password
1. Ative 2FA na sua conta Google
2. Vá em "Senhas de app" nas configurações
3. Gere uma senha específica para o app
4. Use essa senha no `SMTP_PASSWORD`

## 🖥️ Dashboard Web

Acesse http://localhost:8001 para visualizar:

### Funcionalidades
- **Status da Câmera**: Conectividade e informações técnicas
- **Status do Stream**: Estado atual, uptime, reconexões
- **YouTube Live**: Link direto para o stream
- **Controles**: Iniciar, parar, reiniciar stream
- **Logs**: Visualização em tempo real
- **Sistema**: Status de dependências

### API Endpoints

#### GET /api/status
```json
{
  "camera": {
    "online": true,
    "ip": "192.168.69.20",
    "info": {
      "resolution": "1920x1080",
      "fps": "25"
    }
  },
  "stream": {
    "active": true,
    "mode": "camera",
    "uptime": "02:15:30",
    "reconnect_attempts": 0
  },
  "youtube": {
    "video_id": "abc123def456",
    "url": "https://youtube.com/watch?v=abc123def456"
  },
  "system": {
    "ffmpeg_available": true,
    "services_initialized": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### POST /api/start
Inicia o streaming

#### POST /api/stop  
Para o streaming

#### POST /api/restart
Reinicia o streaming

#### GET /api/logs
Retorna logs recentes do sistema

#### GET /api/camera-test
Testa conectividade da câmera

#### POST /api/test-alerts
Testa sistema de alertas

## 🔍 Monitoramento e Logs

### Visualizar Logs
```bash
# Logs do container
docker logs -f camera_streamer

# Logs específicos do dashboard
docker exec camera_streamer tail -f /camera/logs/dashboard.log

# Logs do stream manager
docker exec camera_streamer tail -f /camera/logs/stream_manager.log
```

### Tipos de Log
- `dashboard.log`: Logs da interface web
- `stream_manager.log`: Logs do gerenciamento de stream
- `health_checker.log`: Logs de verificação de saúde
- `alert_service.log`: Logs do sistema de alertas

### Métricas Importantes
- **Uptime do Stream**: Tempo contínuo de streaming
- **Tentativas de Reconexão**: Número de reconexões automáticas
- **Status da Câmera**: Online/offline com detalhes técnicos
- **Latência de Resposta**: Tempo de resposta da API
- **Taxa de Sucesso**: Porcentagem de operações bem-sucedidas

## 🚨 Troubleshooting

### Problemas Comuns

#### Container não inicia
```bash
# Verificar logs de erro
docker logs camera_streamer

# Verificar configuração
docker-compose config

# Verificar arquivo .env
cat .env | grep -v "^#"
```

#### Câmera não conecta
```bash
# Testar ping para câmera
ping 192.168.69.20

# Testar RTSP manualmente
ffprobe rtsp://admin:CoraRosa@192.168.69.20:554/cam/realmonitor?channel=1&subtype=0

# Verificar logs de health check
docker exec camera_streamer tail -f /camera/logs/health_checker.log
```

#### Stream não funciona
```bash
# Verificar chave do YouTube
echo $YOUTUBE_STREAM_KEY

# Testar manualmente
docker exec camera_streamer ffmpeg -rtsp_transport tcp -i $CAMERA_RTSP_URL -f flv $YOUTUBE_RTMP_URL/$YOUTUBE_STREAM_KEY

# Verificar logs do stream
docker exec camera_streamer tail -f /camera/logs/stream_manager.log
```

#### Dashboard não carrega
```bash
# Verificar se porta está aberta
curl http://localhost:8001

# Verificar processo Flask
docker exec camera_streamer ps aux | grep python

# Restart do container
docker-compose restart camera-streamer
```

### Códigos de Erro

- **101**: Falha na conectividade da câmera
- **102**: Erro no processo FFmpeg
- **103**: Falha na autenticação YouTube
- **104**: Limite de reconexões atingido
- **201**: Erro no sistema de alertas
- **301**: Falha na inicialização do dashboard

### Performance

#### Otimização de Resources
```bash
# Verificar uso de CPU/memória
docker stats camera_streamer

# Ajustar bitrate para conexão mais lenta
# No .env: STREAM_BITRATE=1500k

# Reduzir resolução se necessário
# No .env: STREAM_RESOLUTION=1280x720
```

#### Network Troubleshooting
```bash
# Testar conectividade YouTube
ping youtube.com

# Verificar latência
traceroute a.rtmp.youtube.com

# Testar upload de rede
speedtest-cli --upload-only
```

## 🔒 Segurança

### Boas Práticas
- Mantenha credenciais em `.env` e nunca no código
- Use senhas de app do Gmail em vez da senha principal
- Configure firewall para restringir acesso à porta 8001
- Monitore logs regularmente para atividades suspeitas
- Mantenha containers atualizados

### Backup
```bash
# Backup de configurações
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup

# Backup de logs importantes
docker cp camera_streamer:/camera/logs ./backup-logs-$(date +%Y%m%d)
```

## 📈 Integração com ClimaCocal

O sistema integra-se perfeitamente com o projeto ClimaCocal existente:

- **YouTube Video ID**: Lê automaticamente do `views.py` do Django
- **Network Proxy**: Utiliza a network existente do Traefik
- **Logs**: Integra-se com o sistema de logging existente
- **Alertas**: Complementa o sistema de notificações

### Integration Points
```python
# Em /app/myproject/core/views.py
YOUTUBE_VIDEO_ID = "abc123def456"  # Lido automaticamente pelo stream_manager

# Network compartilhada no docker-compose.yml
networks:
  - proxy  # Network existente do Traefik
```

## 🆘 Suporte

### Scripts de Diagnóstico
```bash
# Teste completo
bash test_camera.sh

# Setup completo
bash setup_camera.sh

# Verificação rápida de status
curl -s http://localhost:8001/api/status | python3 -m json.tool
```

### Informações do Sistema
```bash
# Versões importantes
docker --version
docker-compose --version
ffmpeg -version

# Status dos serviços
docker-compose ps
docker network ls | grep proxy
```

### Contato e Issues
Para reportar problemas ou sugestões:
1. Verifique os logs primeiro
2. Execute `test_camera.sh` para diagnóstico
3. Documente o problema com logs relevantes
4. Inclua configuração (sem senhas) se necessário

---

## 📝 Changelog

### v1.0.0 (2024-01-15)
- Sistema inicial de streaming
- Dashboard web completo
- Sistema de alertas Telegram/Email
- Health checking automático
- Fallback para imagem offline
- Integração com YouTube Live
- Scripts de setup e teste
- Documentação completa