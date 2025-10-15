# ClimaCocal - Sistema Integrado de E-commerce e Streaming

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue)](https://www.docker.com/)
[![Django](https://img.shields.io/badge/Django-3.2.25-green)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Microservices-orange)](./ARCHITECTURAL_EVALUATION.md)

Sistema completo de streaming direto e e-commerce com integração MercadoPago, desenvolvido para ClimaCocal com arquitetura de microserviços moderna.

---

## 🎯 Visão Geral

O ClimaCocal é uma plataforma integrada que combina:

- **🛒 E-commerce** - Loja online com integração Mercado Pago
- **📹 Direct Streaming** - Streaming RTSP direto para HLS com controle de acesso
- **📺 YouTube Automation** - Automação de transmissões YouTube Live (legacy)
- **🖥️ Dashboard** - Interface de monitoramento em tempo real
- **🔒 Payment Validation** - Sistema de validação de pagamento por sessão

## 🏗️ Nova Arquitetura (v2.1)

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Django Web App<br/>Port 8000]
        B[Camera Dashboard<br/>Port 8001]
        C[Static Files<br/>nginx]
    end
    
    subgraph "Application Layer"
        D[Streaming Service]
        E[Payment Service]
        F[YouTube Service]
    end
    
    subgraph "Infrastructure Layer"
        G[PostgreSQL<br/>Database]
        H[Redis Cache<br/>Session Store]
        I[FFmpeg<br/>Stream Processor]
    end
    
    subgraph "External Services"
        J[MercadoPago API]
        K[YouTube Live API]
        L[Camera RTSP Stream]
    end
    
    subgraph "Reverse Proxy"
        M[Cloudflare CDN]
        N[Traefik Proxy]
        O[Let's Encrypt SSL]
    end
    
    A --> D
    A --> E
    A --> J
    D --> I
    D --> L
    E --> H
    F --> K
    B --> D
    C --> A
    M --> N
    N --> A
    N --> B
    O --> N
    
    style A fill:#e1f5fe
    style D fill:#e8f5e8
    style E fill:#fff3e0
    style G fill:#fce4ec
    style M fill:#f3e5f5
```

### Componentes Principais

| Componente | Tecnologia | Porta | Função | Status |
|------------|------------|-------|---------|--------|
| **Django App** | Python 3.12 + Django 3.2 | 8000 | E-commerce + Streaming API | ✅ Ativo |
| **Streaming Service** | FFmpeg + HLS | - | Direct camera streaming | ✅ Ativo |
| **Payment Service** | MercadoPago SDK | - | Validação de pagamentos | ✅ Ativo |
| **Camera Dashboard** | Flask + FFmpeg | 8001 | Monitoramento streaming | ✅ Ativo |
| **YouTube Automation** | Python + YouTube API | - | Automação YouTube | 🟡 Legacy |
| **PostgreSQL** | PostgreSQL 15 | 5432 | Database principal | ✅ Ativo |

---

## 🚀 Quick Start

### Pré-requisitos

- **Docker** 20.10+ e **Docker Compose** 1.29+
- **Git** para clonagem do repositório
- **Acesso à rede** para conectar com câmera IP e APIs

### Instalação Rápida

```bash
# 1. Clone o repositório
git clone [repository-url]
cd cocalClima

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais

# 3. Inicie todos os serviços
docker-compose up -d

# 4. Teste a instalação
bash test_ssl_fix.sh
curl -f https://localhost:8000/streaming/api/status/

# 5. Verifique o status
docker-compose ps
```

### Acesso aos Serviços

- **🛒 E-commerce**: https://climacocal.com.br
- **📹 Camera Dashboard**: https://climacocal.com.br:8001
- **📊 Streaming API**: https://climacocal.com.br/streaming/api/
- **🧪 Test Suite**: `python manage.py test` (988 linhas de testes)

---

## ⚙️ Configuração

### Variáveis de Ambiente Essenciais

```bash
# Database
POSTGRES_DB=climacocal_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Django
DJANGO_SECRET_KEY=your_secret_key_here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=climacocal.com.br,www.climacocal.com.br

# Mercado Pago
MERCADO_PAGO_ACCESS_TOKEN=your_mercado_pago_token
MERCADO_PAGO_PUBLIC_KEY=your_mercado_pago_public_key

# Camera Streaming
CAMERA_RTSP_URL=rtsp://user:pass@camera_ip:554/path
STREAM_RESOLUTION=1920x1080
STREAM_FPS=25
STREAM_BITRATE=2500k

# Alertas (opcional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
SMTP_HOST=smtp.gmail.com
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Configuração Detalhada

Consulte a documentação específica:
- **Streaming System**: [STREAMING_IMPLEMENTATION_GUIDE.md](STREAMING_IMPLEMENTATION_GUIDE.md)
- **SSL Configuration**: [SSL_CERTIFICATE_FIX.md](SSL_CERTIFICATE_FIX.md)
- **Architecture Analysis**: [ARCHITECTURAL_EVALUATION.md](ARCHITECTURAL_EVALUATION.md)
- **API Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## 📊 Funcionalidades

### 🛒 E-commerce (Django)
- ✅ Interface responsiva com Bootstrap
- ✅ Integração MercadoPago completa
- ✅ Sistema de pagamento por sessão
- ✅ Callback URLs com fallback SSL
- ✅ Weather API integration

### 📹 Direct Streaming (Novo em v2.1)
- ✅ **Streaming RTSP → HLS** direto (sem YouTube)
- ✅ **Controle de acesso** baseado em pagamento
- ✅ **FFmpeg otimizado** com configurações profissionais
- ✅ **Auto-cleanup** de arquivos HLS antigos
- ✅ **Health monitoring** com reconexão automática
- ✅ **API RESTful** completa com endpoints

#### Streaming API Endpoints
```bash
GET  /streaming/api/status/          # Status e acesso
POST /streaming/api/start/           # Iniciar streaming (admin)
POST /streaming/api/stop/            # Parar streaming (admin)
GET  /streaming/health/              # Health check
GET  /streaming/stream.m3u8          # HLS playlist
GET  /streaming/<segment>.ts         # HLS segments
```

### 📺 YouTube Automation (Legacy)
- 🟡 Criação automática de lives
- 🟡 Configuração de stream
- 🟡 Integração com Django
- ⚠️ **Status**: Substituído por streaming direto

### 🔧 DevOps & Infrastructure
- ✅ **Docker multi-container** com orquestração
- ✅ **Traefik reverse proxy** com SSL automático
- ✅ **Cloudflare integration** com ECH support
- ✅ **Health checks** automatizados
- ✅ **Logging estruturado** por container
- ✅ **TDD completo** com 45+ testes automatizados

---

## 🛠️ Desenvolvimento

### Estrutura do Código (Atualizada)

```
cocalClima/
├── 📦 myproject/                    # Django Application (1.821 linhas)
│   ├── core/                        # Core app (views, templates, static)
│   │   ├── views.py                 # 293 linhas (⚠️ refatoração recomendada)
│   │   ├── templates/               # 5 templates (3 obsoletos)
│   │   └── static/                  # CSS, JS, imagens
│   ├── streaming/                   # ✅ Nova arquitetura streaming (539 linhas)
│   │   ├── services.py              # CameraStreamingService (272 linhas)
│   │   ├── views.py                 # API endpoints (267 linhas)
│   │   ├── urls.py                  # Routing
│   │   └── management/commands/     # Django commands
│   ├── tests/                       # ✅ Suite TDD completa (988 linhas)
│   │   ├── test_streaming_services.py (452 linhas)
│   │   └── test_streaming_views.py    (536 linhas)
│   └── myproject/                   # Django settings
├── 📹 camera/                       # Camera Container (1.142 linhas)
│   ├── scripts/                     # Python modules
│   ├── templates/                   # Flask templates
│   └── requirements.txt
├── 📺 youtube/                      # YouTube Container (178 linhas)
│   ├── scripts/                     # Automation scripts
│   └── credentials/                 # API credentials
├── 🐳 Docker Files                  # Container definitions
│   ├── Dockerfile                   # Django container
│   ├── Dockerfile.camera            # Camera container
│   ├── Dockerfile.youtube           # YouTube container
│   └── docker-compose.yml           # Orchestration
├── 📋 docs/                         # ✅ Documentação unificada (8 arquivos)
│   ├── ARCHITECTURAL_EVALUATION.md  # Análise arquitetural completa
│   ├── STREAMING_IMPLEMENTATION_GUIDE.md
│   ├── SSL_CERTIFICATE_FIX.md
│   └── API_DOCUMENTATION.md
└── 🚨 legacy/ (para remoção)        # 789 linhas de débito técnico
    ├── 22 scripts Python obsoletos
    ├── 70+ arquivos de log antigos
    └── 3 templates com backup dates
```

### Comandos de Desenvolvimento

```bash
# Desenvolvimento local
docker-compose up -d                    # Start all services
docker-compose logs -f streaming        # View streaming logs
docker-compose exec climacocal bash     # Access Django container

# Testing (988 linhas de testes)
python manage.py test                    # Run all Django tests
python manage.py test streaming         # Test streaming module
python manage.py test core              # Test core module
bash test_ssl_fix.sh                    # Test SSL configuration

# Streaming específico
curl -s http://localhost:8000/streaming/api/status/ | jq
curl -X POST http://localhost:8000/streaming/api/start/ \
  -H "Authorization: Bearer admin_token"

# Database
docker-compose exec db psql -U postgres climacocal_db
python manage.py makemigrations
python manage.py migrate

# Build e Deploy
docker-compose build --no-cache         # Clean build
docker-compose up -d --build           # Build and start
```

---

## 🧪 Testing

### Test Strategy (988 linhas)

```bash
# ✅ Streaming Services Tests (452 linhas)
python manage.py test tests.test_streaming_services
# - Camera connection testing
# - FFmpeg process management
# - Payment validation logic
# - Error handling and recovery

# ✅ Streaming Views Tests (536 linhas)  
python manage.py test tests.test_streaming_views
# - API endpoint security
# - HLS file serving
# - Authentication and authorization
# - Legacy compatibility

# Integration Tests
bash test_ssl_fix.sh                    # SSL/TLS validation
curl -f https://climacocal.com.br       # E2E connectivity
```

### Test Coverage

```bash
# Coverage report
coverage run --source='.' manage.py test
coverage report -m
# Current: ~85% coverage na nova arquitetura streaming
```

---

## 📈 Monitoring

### Health Checks

```bash
# Service status
docker-compose ps
curl -f https://climacocal.com.br/streaming/health/

# Resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Streaming status
curl -s https://climacocal.com.br/streaming/api/status/ | jq
```

### Logs

```bash
# Streaming específico
docker logs -f climacocal_app | grep streaming
docker logs -f camera_streamer

# All services
docker-compose logs -f --tail=100

# Log locations
/app/myproject/logs/            # Django logs
/camera/logs/                   # Camera streaming logs
/youtube/scripts/logs/          # YouTube automation logs
```

---

## 🔒 Segurança

### Security Features

- ✅ **HTTPS obrigatório** com Traefik + Let's Encrypt
- ✅ **Cloudflare ECH** support com fallback SSL
- ✅ **Payment callback security** com URLs redundantes
- ✅ **Session-based access** para streaming
- ✅ **Environment isolation** via Docker
- ✅ **API authentication** para endpoints sensíveis

### Security Checklist

```bash
# SSL/TLS validation
bash test_ssl_fix.sh

# Django security check
docker-compose exec climacocal python manage.py check --deploy

# Container security
docker-compose exec climacocal python manage.py diffsettings
```

---

## 🚀 Deployment

### Production Deployment

```bash
# 1. SSL certificates setup
# Certificados automáticos via Traefik + Let's Encrypt + Cloudflare

# 2. Environment configuration
cp .env.production .env
# Configure production values

# 3. Deploy with zero downtime
docker-compose up -d --build

# 4. Verify deployment
bash test_ssl_fix.sh
curl -f https://climacocal.com.br/streaming/api/status/
```

### Scaling

```bash
# Scale Django app
docker-compose up -d --scale climacocal=3

# Load balancer já configurado via Traefik
```

---

## 📚 Documentação

### Documentos Disponíveis

- **[ARCHITECTURAL_EVALUATION.md](ARCHITECTURAL_EVALUATION.md)** - 📊 Avaliação arquitetural completa (6.8/10)
- **[STREAMING_IMPLEMENTATION_GUIDE.md](STREAMING_IMPLEMENTATION_GUIDE.md)** - 📹 Implementação TDD streaming
- **[SSL_CERTIFICATE_FIX.md](SSL_CERTIFICATE_FIX.md)** - 🔒 Correção certificados SSL
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - 📖 Documentação API completa
- **[CAMERA_SETUP.md](CAMERA_SETUP.md)** - 📹 Setup sistema câmera

### API Quick Reference

```bash
# E-commerce
GET  /                                  # Homepage
POST /create-payment/                   # Create MercadoPago payment
GET  /payment-success/                  # Payment success callback
GET  /payment-failure-safe/             # Payment failure (SSL safe)

# Streaming (Novo)
GET  /streaming/api/status/             # Status + access validation
POST /streaming/api/start/              # Start streaming (admin only)
POST /streaming/api/stop/               # Stop streaming (admin only)
GET  /streaming/health/                 # Health check
GET  /streaming/stream.m3u8             # HLS playlist (with payment)
GET  /streaming/<segment>.ts            # HLS segments (with payment)

# Legacy compatibility
GET  /camera/stream.m3u8                # Legacy HLS endpoint
GET  /camera/<segment>                  # Legacy segment endpoint
```

---

## 🤝 Contribuição

### Development Workflow

1. **Fork** o repositório
2. **Clone** sua fork: `git clone [your-fork-url]`
3. **Create branch**: `git checkout -b feature/amazing-feature`
4. **Run tests**: `python manage.py test` (988 linhas)
5. **Commit changes**: `git commit -m 'feat: add amazing feature'`
6. **Push branch**: `git push origin feature/amazing-feature`
7. **Open Pull Request**

### Code Quality

```bash
# Pre-commit checks
python manage.py test                    # All tests must pass
python manage.py check --deploy         # Django deployment check
bash test_ssl_fix.sh                    # SSL configuration test
docker-compose ps                       # All containers healthy
```

---

## 📊 Status do Projeto

### Current Version: 2.1.0 (Direct Streaming)

**🟢 Stable Features:**
- ✅ **Direct Streaming** - Arquitetura RTSP→HLS completa
- ✅ **Payment Integration** - MercadoPago com SSL fallback
- ✅ **TDD Suite** - 988 linhas de testes automatizados
- ✅ **SSL/TLS** - Certificados automáticos + ECH support
- ✅ **Docker Deployment** - Multi-container orquestração

**🟡 Legacy Features:**
- 🟡 **YouTube Automation** - Funcional mas substituído
- 🟡 **Static Documentation** - Fragmentada (8 arquivos)

**🔴 Technical Debt (21.6%):**
- ❌ **789 linhas** de código obsoleto para remoção
- ❌ **67 arquivos** para limpeza (logs, backups, scripts)
- ❌ **core/views.py** - 293 linhas precisam refatoração
- ❌ **Documentação** - Consolidação necessária

### Architectural Score: 6.8/10

**Breakdown:**
- **Streaming Architecture**: 9/10 ✅
- **Security (SSL/TLS)**: 8/10 ✅  
- **Payment Integration**: 8/10 ✅
- **Containerization**: 7/10 ✅
- **Code Quality**: 5/10 ⚠️ (débito técnico)
- **Documentation**: 6/10 ⚠️ (fragmentada)

### Roadmap

**🚨 PRIORIDADE 1 - CRÍTICA (1-2 semanas):**
- Refatoração `core/views.py` (293→4 módulos)
- Limpeza débito técnico (789 linhas obsoletas)
- Consolidação documentação (8→4 arquivos)

**🟡 PRIORIDADE 2 - IMPORTANTE (1 mês):**
- CI/CD pipeline automatizado
- Monitoring e observabilidade
- Performance optimization

**📈 PRIORIDADE 3 - MELHORIA (trimestre):**
- Advanced caching strategies
- Microservices decomposition
- Advanced security hardening

---

## 📞 Suporte

### Troubleshooting

**🔧 Problemas Comuns:**

```bash
# Streaming não funciona
curl -f https://climacocal.com.br/streaming/api/status/
docker logs -f climacocal_app | grep streaming
python manage.py test tests.test_streaming_services

# SSL/ECH errors
bash test_ssl_fix.sh
curl -I https://climacocal.com.br/payment-failure-safe/

# Container não inicia
docker-compose down && docker-compose up -d
docker-compose logs [service_name]

# Payment callback fails
curl -I https://climacocal.com.br/payment-success/
curl -I https://climacocal.com.br/payment-failure-safe/
```

**📖 Debug Commands:**

```bash
# Full system diagnostic
bash test_ssl_fix.sh              # SSL + streaming test
python manage.py test             # 988 linhas de testes
docker-compose ps                 # Service status
curl -f https://climacocal.com.br/streaming/health/

# Architectural analysis
cat ARCHITECTURAL_EVALUATION.md   # Pontuação: 6.8/10
```

---

## 📄 License

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

**Desenvolvido com ❤️ para ClimaCocal**

**Última atualização:** 15 de Outubro de 2025  
**Versão Atual:** 2.1.0 (Direct Streaming Architecture)  
**Próxima Revisão:** Após refatoração arquitetural (Novembro 2025)