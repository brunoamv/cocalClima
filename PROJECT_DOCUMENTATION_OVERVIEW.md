# Documentação Completa do Projeto ClimaCocal
## Overview Técnico e Arquitetural - Versão 2.1.1

---

## 📋 Sumário Executivo

**ClimaCocal** é uma plataforma integrada de **e-commerce com streaming direto** que combina:
- 🛒 **E-commerce** com pagamento via MercadoPago  
- 📹 **Streaming RTSP→HLS** direto da câmera IP
- 🔒 **Controle de acesso** baseado em pagamento por sessão
- 📊 **Interface otimizada** para visualização de dados meteorológicos em tempo real

---

## 🏗️ Arquitetura Técnica

### **Stack Tecnológico**
```yaml
Backend:      Django 3.2.25 + Python 3.12
Frontend:     Bootstrap + Vanilla JS + HLS.js  
Database:     PostgreSQL 15
Streaming:    FFmpeg + HLS Protocol
Containers:   Docker + Docker Compose
Proxy:        Traefik + Let's Encrypt
Payment:      MercadoPago SDK v2.0
SSL/TLS:      Cloudflare ECH + Auto-renewal
```

### **Arquitetura Multi-Container**
```
┌─────────────────────────────────────────────────────────┐
│                  Cloudflare CDN + ECH                  │
├─────────────────────────────────────────────────────────┤
│            Traefik Reverse Proxy + SSL                 │  
├─────────────────────────────────────────────────────────┤
│ Django App    │ PostgreSQL    │ Camera Stream Volume  │
│ (port 8000)   │ (port 5432)   │ (HLS files)          │
├─────────────────────────────────────────────────────────┤
│                   Docker Network                       │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 Estrutura de Código (Total: 5.753 linhas)

### **Core Django Application**
```
myproject/                          (1.821 linhas)
├── core/                           # App principal  
│   ├── views.py                    # Payment + Weather + Legacy (293 linhas)
│   ├── templates/                  # 5 templates HTML
│   │   ├── index.html             # Homepage  
│   │   ├── payment_success.html   # Página pós-pagamento ✨ ATUALIZADA
│   │   └── payment_failure.html   # Página falha pagamento
│   └── static/                     # CSS, JS, imagens
│       ├── css/style.css          # Estilos principais (290 linhas)
│       └── js/script.js           # JavaScript utilities
├── streaming/                      # ✅ Nova arquitetura (539 linhas)  
│   ├── services.py                # CameraStreamingService ✨ OTIMIZADO
│   ├── views.py                   # API RESTful (267 linhas)
│   ├── urls.py                    # Rotas streaming
│   └── management/commands/       # Django commands
└── tests/                         # ✅ TDD Suite (988 linhas)
    ├── test_streaming_services.py # Testes serviços (452 linhas)
    └── test_streaming_views.py    # Testes views (536 linhas)
```

### **Container Services**
```
camera/                             (1.142 linhas)
├── scripts/
│   ├── stream_manager.py          # Gerenciamento FFmpeg (288 linhas)
│   ├── dashboard.py               # Dashboard monitoramento (280 linhas)
│   └── utils.py                   # Utilitários (283 linhas)
└── templates/dashboard.html       # Interface dashboard

docker-compose.yml                  # Orquestração containers (83 linhas)
Dockerfile                         # Build Django + FFmpeg (30 linhas)
requirements.txt                   # Dependências Python
```

### **Documentação** (19 arquivos)
```
Documentação Principal:
├── CLAUDE.md                      # ✨ Contexto para IA (atualizado)
├── README.md                      # Overview do projeto
├── API_DOCUMENTATION.md           # Documentação completa da API
├── ARCHITECTURAL_EVALUATION.md    # Análise arquitetural (6.8/10)
├── STREAMING_IMPLEMENTATION_GUIDE.md # Guia implementação TDD
└── RECENT_CHANGES_2025-10-26.md   # ✨ Mudanças recentes (novo)

Documentação Técnica:
├── SSL_CERTIFICATE_FIX.md         # Correção ERR_ECH_FALLBACK
├── CAMERA_SETUP.md                # Setup câmera IP
├── GIT_OPERATIONS_FINAL.md        # Operações Git
└── CLEANUP_PLAN.md                # Plano limpeza débito técnico
```

---

## 🔧 Componentes Principais

### **1. E-commerce & Payment (Django Core)**
**Localização**: `myproject/core/views.py`  
**Funcionalidades**:
- Homepage com previsão meteorológica
- Integração MercadoPago (pagamento por sessão)
- Callbacks SSL seguros com fallback
- Controle de acesso baseado em cache

**APIs Principais**:
```python
POST /create-payment/           # Criar pagamento MercadoPago
GET  /payment-success/          # Callback sucesso
GET  /payment-failure-safe/     # Callback falha (SSL safe)
GET  /test-payment-direct/      # Simulação pagamento (desenvolvimento)
```

### **2. Streaming Service (Nova Arquitetura)**
**Localização**: `myproject/streaming/`  
**Funcionalidades**:
- Conversão RTSP → HLS em tempo real
- Validação de acesso baseada em pagamento
- API RESTful para controle de streaming
- Detecção inteligente de câmera ✨ **NOVA**

**APIs de Streaming**:
```python
GET  /streaming/api/status/     # Status + validação acesso ✨ OTIMIZADA
POST /streaming/api/start/      # Iniciar streaming (admin)
POST /streaming/api/stop/       # Parar streaming (admin)
GET  /streaming/camera/stream.m3u8  # Playlist HLS (requer pagamento)
```

### **3. UX Otimizada do Player** ✨ **NOVA**
**Localização**: `myproject/core/templates/payment_success.html`  
**Funcionalidades**:
- Controles customizados externos ao vídeo
- Preservação de informações da câmera (hora/data)
- Design responsivo e moderno
- Suporte fullscreen e controle de áudio

**Características**:
- **Layout**: 3 seções (controles, status, fullscreen)
- **Compatibilidade**: Cross-browser incluindo Safari
- **Performance**: JavaScript vanilla (sem dependências)
- **Acessibilidade**: Controles com ícones e ARIA labels

---

## 🧪 Qualidade e Testes

### **Test-Driven Development**
```bash
# Suite completa de testes (988 linhas)
python manage.py test                          # Todos os testes
python manage.py test tests.test_streaming_services  # 452 linhas
python manage.py test tests.test_streaming_views     # 536 linhas

# Cobertura: ~85% na nova arquitetura streaming
```

### **Scripts de Validação**
```bash
# Validação SSL/TLS + streaming
bash test_ssl_fix.sh

# Health checks automáticos  
curl -f /streaming/api/status/
docker-compose ps
```

---

## 🔒 Segurança e SSL

### **Stack SSL/TLS**
- **Cloudflare**: ECH (Encrypted Client Hello) support
- **Traefik**: Let's Encrypt automation + reverse proxy
- **Headers**: Security headers automáticos
- **Fallback**: URLs redundantes para problemas ECH

### **Payment Security**
- **Callbacks duplos**: Principal + safe fallback  
- **Session validation**: Cache-based access control
- **HTTPS enforcement**: Redirecionamento automático
- **MercadoPago integration**: SDK oficial com webhooks seguros

---

## 📊 Métricas e Performance

### **Pontuação Arquitetural**: 6.8/10
| Componente | Score | Status |
|------------|-------|--------|
| **Streaming Architecture** | 9/10 | ✅ Excelente |
| **Security (SSL/TLS)** | 8/10 | ✅ Muito bom |
| **Payment Integration** | 8/10 | ✅ Muito bom |
| **UX/UI** | 8/10 | ✅ Otimizada ✨ |
| **Containerization** | 7/10 | ✅ Bom |
| **Code Quality** | 5/10 | ⚠️ Débito técnico |
| **Documentation** | 7/10 | ✅ Melhorada ✨ |

### **Distribuição de Código**
- **Produtivo**: 3.164 linhas (55.0%) ✅
- **Débito técnico**: 789 linhas (13.7%) ⚠️ 
- **Testes**: 988 linhas (17.2%) ✅
- **Documentação**: 19 arquivos ✅

---

## 🚨 Status e Próximos Passos

### **Estado Atual**: ✅ **PRODUÇÃO ESTÁVEL**
- ✅ Stream detection: Funcionando  
- ✅ Payment flow: Operacional
- ✅ UX player: Otimizada
- ✅ SSL/TLS: Estável
- ✅ API endpoints: Ativos

### **Prioridades Técnicas**:
1. **CRITICAL**: Limpeza de débito técnico (789 linhas - 13.7%)
2. **HIGH**: Refatoração `core/views.py` (293 → 4 módulos)  
3. **MEDIUM**: Consolidação documentação (19 → 12 arquivos)
4. **LOW**: CI/CD pipeline automatizado

---

## 🛠️ Comandos de Desenvolvimento

### **Local Development**
```bash
# Inicializar ambiente
docker-compose up -d

# Executar testes  
python manage.py test

# Verificar API
curl -s /streaming/api/status/ 

# Validação SSL
bash test_ssl_fix.sh
```

### **Debugging**
```bash
# Logs containers
docker-compose logs -f climacocal_app

# Django shell
docker-compose exec climacocal_app python manage.py shell

# Database access
docker-compose exec db psql -U postgres climacocal_db
```

### **Production Deployment**
```bash
# Build e deploy
docker-compose build --no-cache
docker-compose up -d --build

# Health check
curl -f https://climacocal.com.br/streaming/health/
```

---

## 🔄 Histórico de Mudanças Recentes

### **26 de Outubro de 2025**
1. ✅ **Stream Detection Fix**: Correção detecção câmera offline
2. ✅ **UX Player Improvement**: Controles customizados sem sobreposição  
3. ✅ **Documentation Update**: CLAUDE.md e relatórios atualizados

### **15 de Outubro de 2025**  
1. ✅ **SSL Certificate Fix**: Correção ERR_ECH_FALLBACK_CERTIFICATE_INVALID
2. ✅ **Architectural Analysis**: Avaliação completa (6.8/10)

---

**Última Atualização**: 26 de Outubro de 2025  
**Versão do Projeto**: 2.1.1 (Optimized UX & Stream Detection)  
**Status**: Produção Estável ✅