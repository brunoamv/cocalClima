# 🔧 Plano de Refatoração core/views.py - ClimaCocal

## 📊 Análise Executiva

### **Arquivo Atual**: `core/views.py` (318 linhas)
### **Status**: God Object com 5 responsabilidades misturadas
### **Objetivo**: Modularização seguindo Single Responsibility Principle

---

## 🔍 Responsabilidades Identificadas

### **1. Home & Navigation** (17 linhas)
```python
def home(request):  # Linha 16-17
```

### **2. YouTube Integration (Legacy)** (49 linhas)
```python
def check_youtube_live(request):     # Linhas 20-40
def get_stream_url(request):         # Linhas 42-49 (parte legacy)
# Hardcoded: YOUTUBE_VIDEO_ID = "zsGnr5FT-Qw"
```

### **3. Payment System** (138 linhas)
```python
def create_payment(request):         # Linhas 51-92
def payment_success(request):        # Linhas 95-98
def test_payment_success(request):   # Linhas 100-107
def test_payment_direct(request):    # Linhas 109-122
def payment_failure(request):        # Linhas 124-134
def payment_failure_safe(request):   # Linhas 136-159
def payment_webhook(request):        # Linhas 162-171
def check_payment_status(request):   # Linhas 174-176
# Hardcoded: MERCADO_PAGO_ACCESS_TOKEN, email, test credentials
```

### **4. Weather API** (10 linhas)
```python
def get_weather(request):           # Linhas 179-188
# Hardcoded: API_TOKEN, CITY_ID
```

### **5. Camera Streaming (Mixed)** (104 linhas)
```python
def camera_stream(request):         # Linhas 193-225
def camera_segment(request, segment_name):  # Linhas 228-262
def camera_status_api(request):     # Linhas 265-276
def get_access_message(payment_status, camera_available):  # Linhas 279-286
def get_stream_url(request):        # Linhas 290-318 (versão híbrida)
# Path hardcoded: "/app/camera_stream/"
```

---

## 🏗️ Estrutura Modular Proposta

### **FASE 1: Criar Services Layer**
```
myproject/core/
├── services/               # 🆕 Novo diretório
│   ├── __init__.py
│   ├── payment_service.py     # MercadoPago logic
│   ├── youtube_service.py     # YouTube API logic
│   ├── weather_service.py     # ClimaTempo API logic
│   └── camera_service.py      # Camera HLS logic (legacy)
└── views/                  # 🆕 Novo diretório
    ├── __init__.py
    ├── home_views.py          # Home & navigation
    ├── payment_views.py       # Payment callbacks
    ├── api_views.py           # API endpoints
    └── legacy_views.py        # Deprecated functions
```

### **FASE 2: Migrar para Streaming App**
```
myproject/streaming/        # ✅ Já existe arquitetura moderna
├── services/
│   ├── camera_service.py      # ✅ Já existe (272 linhas)
│   ├── payment_service.py     # 🔄 Consolidar com core
│   └── youtube_service.py     # 🔄 Migrar do core
├── views/
│   ├── streaming_views.py     # ✅ Já existe (267 linhas)
│   ├── payment_api.py         # 🆕 Payment API
│   └── legacy_api.py          # 🆕 YouTube + Weather APIs
```

---

## 🔧 Detalhamento da Refatoração

### **1. PaymentService (138 linhas → 45 linhas)**
```python
# core/services/payment_service.py
class PaymentService:
    def __init__(self):
        self.sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    
    def create_preference(self, title: str, price: float) -> dict:
        """Create MercadoPago payment preference"""
        
    def validate_webhook(self, data: dict) -> bool:
        """Validate MercadoPago webhook"""
        
    def set_payment_status(self, status: str, timeout: int = 600):
        """Set payment status in cache"""
        
    def get_payment_status(self) -> str:
        """Get current payment status"""
```

### **2. YouTubeService (49 linhas → 25 linhas)**
```python
# core/services/youtube_service.py
class YouTubeService:
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        self.video_id = settings.YOUTUBE_VIDEO_ID
    
    def check_live_status(self) -> dict:
        """Check if YouTube live is active"""
        
    def get_embed_url(self) -> str:
        """Get YouTube embed URL"""
```

### **3. WeatherService (10 linhas → 8 linhas)**
```python
# core/services/weather_service.py
class WeatherService:
    def __init__(self):
        self.api_token = settings.WEATHER_API_TOKEN
        self.city_id = settings.WEATHER_CITY_ID
    
    def get_current_weather(self) -> dict:
        """Get current weather data"""
```

### **4. CameraService Legacy (104 linhas)**
**Destino**: Consolidar com `streaming/services/camera_service.py` existente
- Migrar lógica HLS para arquitetura moderna
- Remover duplicação de responsabilidades

---

## 📋 Configuração Necessária

### **settings.py Additions**
```python
# Payment Configuration
MERCADO_PAGO_ACCESS_TOKEN = os.environ.get('MERCADO_PAGO_ACCESS_TOKEN')

# YouTube Configuration
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
YOUTUBE_VIDEO_ID = os.environ.get('YOUTUBE_VIDEO_ID', 'zsGnr5FT-Qw')

# Weather Configuration
WEATHER_API_TOKEN = os.environ.get('WEATHER_API_TOKEN', '546659d2c8b489261f185e4e10b21d3c')
WEATHER_CITY_ID = os.environ.get('WEATHER_CITY_ID', '3137')

# Camera Configuration
CAMERA_STREAM_PATH = os.environ.get('CAMERA_STREAM_PATH', '/app/camera_stream/')
```

### **URLs Reorganization**
```python
# core/urls.py
urlpatterns = [
    path('', home_views.home, name='home'),
    path('create-payment/', payment_views.create_payment, name='create_payment'),
    path('payment-success/', payment_views.payment_success, name='payment_success'),
    path('payment-failure/', payment_views.payment_failure, name='payment_failure'),
    path('payment-failure-safe/', payment_views.payment_failure_safe, name='payment_failure_safe'),
    
    # API endpoints
    path('api/payment/status/', api_views.payment_status, name='api_payment_status'),
    path('api/weather/', api_views.weather, name='api_weather'),
    path('api/youtube/live/', api_views.youtube_live_check, name='api_youtube_live'),
    
    # Legacy endpoints (deprecate)
    path('legacy/', include('core.urls_legacy')),
]
```

---

## 🧪 Estratégia TDD

### **1. Criar Testes para Services**
```python
# tests/test_payment_service.py
class PaymentServiceTest(TestCase):
    def test_create_preference_success(self):
    def test_validate_webhook_data(self):
    def test_payment_status_cache(self):

# tests/test_youtube_service.py  
class YouTubeServiceTest(TestCase):
    def test_check_live_status_active(self):
    def test_check_live_status_inactive(self):

# tests/test_weather_service.py
class WeatherServiceTest(TestCase):
    def test_get_current_weather_success(self):
```

### **2. Criar Testes para Refactored Views**
```python
# tests/test_refactored_views.py
class RefactoredViewsTest(TestCase):
    def test_payment_views_use_service(self):
    def test_api_endpoints_consistency(self):
    def test_backward_compatibility(self):
```

### **3. Migration Tests**
```python
# tests/test_migration_compatibility.py
class MigrationCompatibilityTest(TestCase):
    def test_old_urls_still_work(self):
    def test_api_responses_identical(self):
    def test_payment_flow_unchanged(self):
```

---

## 🔄 Plano de Execução

### **FASE 1: Preparação (Seguro)**
1. ✅ **Backup**: Commit atual com `git add -A && git commit -m "backup: antes da refatoração core/views.py"`
2. 🔄 **Criar estrutura**: Diretórios `core/services/` e `core/views/`
3. 🔄 **Criar Services**: Implementar PaymentService, YouTubeService, WeatherService
4. 🔄 **Criar Testes**: TDD para cada service
5. 🔄 **Validar**: `python manage.py test tests.test_*_service`

### **FASE 2: Refatoração (Incremental)**
1. 🔄 **Extrair Payment Views**: Mover lógica de pagamento para payment_views.py
2. 🔄 **Extrair API Views**: Consolidar APIs em api_views.py
3. 🔄 **Extrair Home Views**: Simples home_views.py
4. 🔄 **Manter Legacy**: core/views.py como proxy temporário
5. 🔄 **Atualizar URLs**: Novo roteamento
6. 🔄 **Validar**: TDD completo + integração

### **FASE 3: Consolidação (Limpeza)**
1. 🔄 **Migrar Camera Logic**: Para streaming app
2. 🔄 **Remover core/views.py**: Arquivo original obsoleto
3. 🔄 **Documentar**: Atualizar API documentation
4. 🔄 **Deploy**: Validação em produção

---

## 📊 Impacto Esperado

### **Antes da Refatoração**
- **core/views.py**: 318 linhas, 5 responsabilidades
- **Complexidade**: 9/10 (God Object)
- **Testabilidade**: 3/10 (Código acoplado)
- **Manutenibilidade**: 4/10 (Hardcoded configs)

### **Após a Refatoração**
- **Arquivos**: 8 módulos bem definidos
- **Complexidade**: 3/10 (Single Responsibility)
- **Testabilidade**: 9/10 (Services testáveis)
- **Manutenibilidade**: 8/10 (Configuração centralizada)

### **Benefícios**
- ✅ **Single Responsibility**: Cada classe tem uma responsabilidade
- ✅ **Testabilidade**: Services isolados e testáveis
- ✅ **Configuração**: Settings centralizados em `settings.py`
- ✅ **Reutilização**: Services reutilizáveis em outros apps
- ✅ **Manutenção**: Código organizado e bem estruturado
- ✅ **Backward Compatibility**: URLs e APIs mantidas

---

## ⚠️ Considerações de Segurança

### **Configuração Segura**
- ❌ **Remover hardcoded credentials** das linhas 63, 76-79
- ❌ **Remover hardcoded API tokens** das linhas 182-183
- ✅ **Usar environment variables** para todas as configurações
- ✅ **Implementar validação** de entrada em todos os services

### **Migração Segura**
- ✅ **Manter backward compatibility** durante a transição
- ✅ **Validar TDD** em cada etapa
- ✅ **Rollback plan** com git commits incrementais

---

**Refatoração validada**: 26 de Outubro de 2025  
**Status**: Pronto para execução com segurança TDD  
**Impacto**: God Object (318 linhas) → 8 módulos bem definidos