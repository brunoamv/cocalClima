# CLAUDE.md - Contexto ClimaCocal para Assistente IA

## 📋 Informações do Projeto

### **Nome**: ClimaCocal
### **Versão**: 2.1.1 (Optimized UX & Stream Detection)
### **Última Atualização**: 26 de Outubro de 2025
### **Status**: PRODUÇÃO ESTÁVEL ✅

---

## 🎯 Objetivo Central

Sistema integrado de **e-commerce com streaming direto** que combina:
- 🛒 **E-commerce** com integração MercadoPago
- 📹 **Streaming RTSP→HLS** direto da câmera (substitui YouTube)
- 🔒 **Controle de acesso** baseado em pagamento por sessão
- 📊 **Dashboard** de monitoramento em tempo real

---

## 🏗️ Arquitetura Atual

### **Stack Tecnológico**
```yaml
Backend:      Django 3.2.25 + Python 3.12
Frontend:     Bootstrap + Vanilla JS + HLS.js
Database:     PostgreSQL 15
Cache:        Django Cache Framework
Streaming:    FFmpeg + HLS
Containers:   Docker + Docker Compose
Proxy:        Traefik + nginx
SSL:          Let's Encrypt + Cloudflare ECH
Payment:      MercadoPago SDK
```

### **Arquitetura Multi-Container**
```
┌─────────────────────────────────────────────────────────┐
│                  Cloudflare CDN + ECH                  │
├─────────────────────────────────────────────────────────┤
│                 Traefik Reverse Proxy                  │
├─────────────────────────────────────────────────────────┤
│ nginx     │ climacocal   │ youtube-auto │ camera      │
│ (static)  │ (django)     │ (legacy)     │ (stream)    │
├─────────────────────────────────────────────────────────┤
│                    PostgreSQL DB                       │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 Estrutura de Arquivos

### **Core Application** (1.821 linhas)
```
myproject/
├── core/                    # App principal (293 linhas)
│   ├── views.py             # ⚠️ REFATORAR: Payment + Weather + YouTube legacy
│   ├── templates/           # 5 templates (3 obsoletos para remoção)
│   └── static/              # CSS, JS, imagens
├── streaming/               # ✅ Nova arquitetura (539 linhas)
│   ├── services.py          # CameraStreamingService (272 linhas)
│   ├── views.py             # API RESTful (267 linhas)
│   └── management/commands/ # Django commands
└── tests/                   # ✅ TDD Suite completa (988 linhas)
    ├── test_streaming_services.py (452 linhas)
    └── test_streaming_views.py    (536 linhas)
```

### **Container Services**
```
camera/                      # Streaming container (1.142 linhas)
├── scripts/stream_manager.py   (288 linhas)
├── scripts/dashboard.py        (280 linhas)
├── scripts/utils.py            (283 linhas)

youtube/                     # ⚠️ Legacy container (178 linhas)
├── scripts/ScriptAutomacao_YT.py (152 linhas)
```

### **🚨 Débito Técnico** (789 linhas - 21.6% do projeto)
```
Root/ (para remoção imediata)
├── 22 scripts Python obsoletos (direct_*.py, force_*.py, etc.)
├── 70+ arquivos de log antigos (scripts/logs/update_project_2025-*.log)
├── 3 templates obsoletos (index_Old.html, *_20250408.html)
└── docker-compose copy.yml
```

---

## 🔧 Componentes Principais

### **1. E-commerce Django**
- **Localização**: `myproject/core/views.py`
- **Funcionalidades**: Homepage, pagamento MercadoPago, callbacks SSL
- **APIs**:
  - `POST /create-payment/` - Criar pagamento
  - `GET /payment-success/` - Callback sucesso
  - `GET /payment-failure-safe/` - Callback falha (SSL safe)

### **2. Streaming Service** ⭐ NOVA ARQUITETURA
- **Localização**: `myproject/streaming/`
- **Funcionalidades**: RTSP→HLS, controle acesso, API RESTful
- **APIs**:
  - `GET /streaming/api/status/` - Status + validação acesso
  - `POST /streaming/api/start/` - Iniciar streaming (admin)
  - `POST /streaming/api/stop/` - Parar streaming (admin)
  - `GET /streaming/stream.m3u8` - Playlist HLS (requer pagamento)

### **3. Payment Validation**
- **Cache-based sessions**: Django cache para controle de acesso
- **Timeout**: 600 segundos (10 minutos) por pagamento
- **Integração**: MercadoPago com callbacks redundantes SSL

### **4. Camera Integration**
- **RTSP Input**: `rtsp://admin:CoraRosa@192.168.3.62:554/cam/realmonitor?channel=1&subtype=0`
- **HLS Output**: Segmentos `.ts` + playlist `.m3u8`
- **FFmpeg**: Configuração otimizada para streaming

---

## 🧪 Testes e Qualidade

### **Test-Driven Development** ✅
```bash
# 988 linhas de testes automatizados
python manage.py test                      # Todos os testes
python manage.py test tests.test_streaming_services  # 452 linhas
python manage.py test tests.test_streaming_views     # 536 linhas

# Cobertura: ~85% na nova arquitetura streaming
```

### **Scripts de Validação**
```bash
bash test_ssl_fix.sh           # SSL/TLS + streaming validation
curl -f /streaming/api/status/  # API health check
docker-compose ps               # Container status
```

---

## 🔒 Segurança e SSL

### **SSL/TLS Stack**
- **Cloudflare**: ECH (Encrypted Client Hello) support
- **Traefik**: Let's Encrypt automation + reverse proxy
- **Fallback**: URLs redundantes para problemas ECH
- **Headers**: Security headers automáticos

### **Payment Security**
- **Callback URLs**: Duplas (principal + safe fallback)
- **Session validation**: Cache-based access control
- **HTTPS obrigatório**: Redirecionamento automático

---

## 📊 Métricas Arquiteturais

### **Pontuação Geral**: 6.8/10 ⚠️

| Componente | Pontuação | Status |
|------------|-----------|--------|
| **Streaming Architecture** | 9/10 | ✅ Excelente |
| **Security (SSL/TLS)** | 8/10 | ✅ Muito bom |
| **Payment Integration** | 8/10 | ✅ Muito bom |
| **Containerization** | 7/10 | ✅ Bom |
| **Code Quality** | 5/10 | ⚠️ Débito técnico |
| **Documentation** | 6/10 | ⚠️ Fragmentada |

### **Distribuição de Código** (Total: 5.753 linhas)
- **Produtivo**: 3.164 linhas (55.0%) ✅ 
- **Débito técnico**: 789 linhas (13.7%) ⚠️
- **Testes**: 988 linhas (17.2%) ✅
- **Documentação**: 19 arquivos ✅

---

## 🚨 Pontos Críticos

### **PRIORIDADE 1 - CRÍTICA**
1. **Refatorar core/views.py** (293 linhas → 4 módulos)
2. **Remover 789 linhas** de código obsoleto
3. **Limpar 67 arquivos** de débito técnico

### **PRIORIDADE 2 - IMPORTANTE**
1. **Consolidar documentação** (8 → 4 arquivos)
2. **CI/CD pipeline** automatizado
3. **Monitoring** e observabilidade

---

## 🛠️ Comandos Essenciais

### **Development**
```bash
# Start all services
docker-compose up -d

# Test suite completa
python manage.py test

# Streaming API test
curl -s /streaming/api/status/ | jq

# SSL validation
bash test_ssl_fix.sh
```

### **Debugging**
```bash
# Container logs
docker-compose logs -f climacocal
docker logs -f camera_streamer

# Django shell
docker-compose exec climacocal python manage.py shell

# Database access
docker-compose exec db psql -U postgres climacocal_db
```

### **Deployment**
```bash
# Production build
docker-compose build --no-cache
docker-compose up -d --build

# Health check
curl -f https://climacocal.com.br/streaming/health/
```

---

## 📚 Documentação Disponível

### **Principais Documentos**
1. **[README.md](README.md)** - Overview completo do projeto
2. **[ARCHITECTURAL_EVALUATION.md](ARCHITECTURAL_EVALUATION.md)** - Análise arquitetural (6.8/10)
3. **[STREAMING_IMPLEMENTATION_GUIDE.md](STREAMING_IMPLEMENTATION_GUIDE.md)** - Implementação TDD streaming
4. **[SSL_CERTIFICATE_FIX.md](SSL_CERTIFICATE_FIX.md)** - Correção SSL/ECH
5. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Documentação API completa

### **Legacy Documentation** (para consolidação)
- `CAMERA_SETUP.md` ⚠️ (consolidar em README)
- `README_YOUTUBE.md` ⚠️ (obsoleto - YouTube substituído)
- `YOUTUBE_AUTH_INSTRUCTIONS.md` ⚠️ (legacy)

---

## 🎯 Contexto para IA

### **Quando Trabalhar Neste Projeto**
1. **Sempre verificar** a arquitetura atual no `ARCHITECTURAL_EVALUATION.md`
2. **Rodar testes** antes de modificações: `python manage.py test`
3. **Usar nova arquitetura streaming** em `myproject/streaming/`
4. **Evitar modificar** arquivos marcados como legacy ou obsoletos

### **Padrões a Seguir**
- **TDD**: Sempre criar/atualizar testes
- **API RESTful**: Seguir padrões do `streaming` app
- **Docker-first**: Todas as modificações devem funcionar em containers
- **SSL-aware**: Considerar problemas ECH/Cloudflare

### **Padrões a Evitar**
- ❌ **Não adicionar** código em `core/views.py` (refatoração pendente)
- ❌ **Não usar** arquivos legacy na raiz (direct_*.py, force_*.py)
- ❌ **Não integrar** YouTube (substituído por streaming direto)
- ❌ **Não criar** arquivos temporários sem limpeza

---

## 🔄 Status da Sessão

### **Trabalho Recente Completado**
1. ✅ **SSL Certificate Fix** - Correção ERR_ECH_FALLBACK_CERTIFICATE_INVALID
2. ✅ **Architectural Analysis** - Avaliação completa (6.8/10)
3. ✅ **Stream Detection Fix** - Correção detecção câmera offline (26/10/2025)
4. ✅ **UX Player Improvement** - Controles customizados sem sobreposição (26/10/2025)
5. ✅ **Documentation Update** - CLAUDE.md e relatórios técnicos atualizados
6. 🔄 **Próximo**: Limpeza de débito técnico (789 linhas obsoletas)

### **Próximas Tarefas Sugeridas**
1. **Refatoração crítica**: `core/views.py` (293 → 4 módulos)
2. **Limpeza**: Remover 67 arquivos obsoletos
3. **Consolidação docs**: 8 → 4 arquivos de documentação
4. **CI/CD**: Pipeline automatizado

---

**💡 Dica para IA**: Este projeto tem arquitetura sólida (streaming 9/10) mas débito técnico significativo (21.6%). Priorize limpeza e refatoração antes de novas features.