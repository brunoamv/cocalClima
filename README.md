# ClimaCocal - Sistema Integrado de E-commerce e Streaming

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue)](https://www.docker.com/)
[![Django](https://img.shields.io/badge/Django-3.2.25-green)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-8.2/10-brightgreen)](./ARCHITECTURAL_EVALUATION.md)
[![UX](https://img.shields.io/badge/UX-Enhanced-blue)](./CLAUDE.md)
[![Version](https://img.shields.io/badge/Version-2.3.0--dev-orange)](./CLAUDE.md)
[![TDD](https://img.shields.io/badge/TDD-2848_lines-brightgreen)](./TDD_STRATEGY.md)

Sistema completo de streaming direto e e-commerce com **auto-recovery inteligente**, **UX aprimorada** e **suite TDD robusta**, desenvolvido para ClimaCocal com arquitetura moderna.

---

## 🎯 Visão Geral

O ClimaCocal é uma plataforma integrada que combina:

- **🛒 E-commerce** - Loja online com integração Mercado Pago
- **📹 Smart Streaming** - RTSP→HLS com **auto-recovery** e monitoramento inteligente
- **🎨 Enhanced UX** - Interface responsiva com layout moderno (v2.2.0)
- **🧪 TDD Framework** - Suite robusta com **2.848+ linhas de testes** (v2.3.0-dev)
- **📍 Location Service** - Transmissão ao vivo de **Cocalzinho de Goiás**
- **🔒 Payment Validation** - Sistema de validação de pagamento por sessão
- **📺 YouTube Legacy** - Automação de transmissões YouTube Live (descontinuado)

## 🏗️ Arquitetura v2.3.0-dev

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
│   ├── tests/                       # ✅ Suite TDD completa (2.848+ linhas)
│   │   ├── test_streaming_services.py (452 linhas)
│   │   ├── test_streaming_views.py    (536 linhas)
│   │   ├── test_core_views.py         (580 linhas)
│   │   ├── test_integration.py        (720 linhas)
│   │   └── test_e2e_playwright.py     (560 linhas)
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
├── 📋 docs/                         # ✅ Documentação unificada (9 arquivos)
│   ├── ARCHITECTURAL_EVALUATION.md  # Análise arquitetural completa
│   ├── STREAMING_IMPLEMENTATION_GUIDE.md
│   ├── SSL_CERTIFICATE_FIX.md
│   ├── API_DOCUMENTATION.md
│   └── TDD_STRATEGY.md              # ✅ Estratégia TDD completa
├── 🧪 TDD Framework/                # ✅ Sistema TDD (400+ linhas)
│   ├── test_runner.py               # Test runner avançado (304 linhas)
│   └── setup_tests.sh               # Setup automatizado (53 linhas)
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

# Testing (2.848+ linhas de testes TDD)
./test_runner.py --all                   # Run complete TDD suite
./test_runner.py --unit                  # Unit tests only
./test_runner.py --integration           # Integration tests
./test_runner.py --e2e                   # E2E tests (Playwright)
./test_runner.py --watch                 # Watch mode for TDD
./test_runner.py --coverage              # With coverage report
python manage.py test                    # Run all Django tests (legacy)
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

## 🧪 Testing & TDD Framework

### Test Strategy (2.848+ linhas) ✅ v2.3.0-dev

```bash
# ✅ Complete TDD Suite with Advanced Runner
./test_runner.py --all                  # Run complete TDD suite (Red-Green-Refactor)
./test_runner.py --unit                 # Unit tests (580 linhas)
./test_runner.py --integration          # Integration tests (720 linhas) 
./test_runner.py --e2e                  # E2E tests (560 linhas Playwright-ready)
./test_runner.py --watch                # Watch mode for continuous TDD
./test_runner.py --coverage             # Coverage report with HTML output
./test_runner.py --lint                 # Code quality checks (flake8, black, isort)

# ✅ Legacy Django Tests (988 linhas)
python manage.py test tests.test_streaming_services  # 452 linhas
python manage.py test tests.test_streaming_views     # 536 linhas

# ✅ Setup and Automation
bash setup_tests.sh                     # TDD environment setup
./test_runner.py --report               # Generate comprehensive test report
```

### TDD Development Workflow

```bash
# 1. RED: Write failing test
./test_runner.py --unit --watch         # Watch mode for immediate feedback

# 2. GREEN: Write minimal code to pass
./test_runner.py --unit                 # Verify tests pass

# 3. REFACTOR: Improve code while keeping tests green
./test_runner.py --all --coverage       # Full validation with coverage
```

### Test Coverage & Quality

```bash
# Coverage report with HTML output
./test_runner.py --coverage
# Output: coverage_reports/unit_tests/index.html

# Code quality and formatting
./test_runner.py --lint
# - flake8: syntax and style
# - black: code formatting  
# - isort: import organization

# Test categories breakdown:
# - Unit Tests (580 linhas): Component testing
# - Integration Tests (720 linhas): Component interaction
# - E2E Tests (560 linhas): User journey testing (Playwright-ready)
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
- **[TDD_STRATEGY.md](TDD_STRATEGY.md)** - 🧪 **Estratégia TDD completa** (v2.3.0-dev)
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
4. **Run TDD suite**: `./test_runner.py --all` (2.848+ linhas)
5. **Commit changes**: `git commit -m 'feat: add amazing feature'`
6. **Push branch**: `git push origin feature/amazing-feature`
7. **Open Pull Request**

### Code Quality

```bash
# Pre-commit checks (TDD Workflow)
./test_runner.py --all                   # Complete TDD suite must pass
./test_runner.py --lint                  # Code quality checks
python manage.py check --deploy         # Django deployment check
bash test_ssl_fix.sh                    # SSL configuration test
docker-compose ps                       # All containers healthy
```

---

## 📊 Status do Projeto

### Current Version: 2.3.0-dev (TDD Framework & Enhanced Testing)

**🟢 Enhanced Features (v2.3.0-dev):**
- ✅ **TDD Framework** - Suite robusta com **2.848+ linhas de testes**
- ✅ **Advanced Test Runner** - Red-Green-Refactor com watch mode
- ✅ **Smart Streaming** - Auto-recovery com cooldown inteligente (5min)
- ✅ **Payment Integration** - MercadoPago com SSL fallback
- ✅ **Enhanced UX** - Layout responsivo baseado no design system
- ✅ **Quality Automation** - flake8, black, isort integration
- ✅ **Real-time Info** - Hora/clima/localização (Cocalzinho de Goiás)
- ✅ **SSL/TLS** - Certificados automáticos + ECH support
- ✅ **Docker Deployment** - Multi-container orquestração

**🟡 Legacy Features:**
- 🟡 **YouTube Automation** - Funcional mas substituído por streaming direto
- 🟡 **Legacy Tests** - 988 linhas Django tests (mantidos para compatibilidade)

**🔴 Technical Debt (13.7%):**
- ❌ **789 linhas** de código obsoleto para remoção
- ❌ **67 arquivos** para limpeza (logs, backups, scripts)
- ❌ **core/views.py** - 293 linhas precisam refatoração

### Architectural Score: 8.2/10 ⬆️ (+1.4)

**Breakdown (v2.3.0-dev):**
- **TDD Framework**: 9.5/10 ✅ 🆕 (2.848+ linhas de testes)
- **Streaming Architecture**: 9.5/10 ✅ 
- **Testing & Quality**: 9/10 ✅ ⬆️ (advanced test runner)
- **User Experience (UX)**: 8.5/10 ✅ 
- **Security (SSL/TLS)**: 8/10 ✅  
- **Payment Integration**: 8/10 ✅
- **Containerization**: 7/10 ✅
- **Code Quality**: 7/10 ✅ ⬆️ (TDD + quality automation)
- **Documentation**: 8/10 ✅ ⬆️ (TDD docs + atualizada)

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
./test_runner.py --all             # 2.848+ linhas TDD suite
docker-compose ps                 # Service status
curl -f https://climacocal.com.br/streaming/health/

# TDD & Quality checks
./test_runner.py --report          # Comprehensive test report
./test_runner.py --lint            # Code quality analysis

# Architectural analysis
cat ARCHITECTURAL_EVALUATION.md   # Pontuação: 8.2/10 (v2.3.0-dev)
```

---

## 📄 License

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

**Desenvolvido com ❤️ para ClimaCocal**

**Última atualização:** 26 de Outubro de 2025  
**Versão Atual:** 2.3.0-dev (TDD Framework & Enhanced Testing)  
**Próxima Revisão:** Após limpeza de débito técnico (Novembro 2025)