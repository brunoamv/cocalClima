# 📡 API de Streaming ClimaCocal v2.2.0

## 🆕 Release: Enhanced UX & Auto-Recovery (26/10/2025)

## Endpoints da API

### 🎥 Streaming Endpoints

#### GET `/streaming/camera/stream.m3u8`
Serve a playlist HLS para usuários autenticados via pagamento.

**Headers de Resposta:**
```
Content-Type: application/vnd.apple.mpegurl
Cache-Control: no-cache, no-store, must-revalidate
Access-Control-Allow-Origin: *
```

**Responses:**
- `200 OK`: Playlist HLS retornada
- `403 Forbidden`: Pagamento necessário
- `503 Service Unavailable`: Câmera indisponível

#### GET `/streaming/camera/<segment_name>`
Serve segmentos de vídeo HLS (.ts files).

**Parâmetros:**
- `segment_name`: Nome do segmento (formato: `segment_XXX.ts`)

**Headers de Resposta:**
```
Content-Type: video/mp2t
Cache-Control: public, max-age=3600
Access-Control-Allow-Origin: *
```

**Responses:**
- `200 OK`: Segmento de vídeo retornado
- `403 Forbidden`: Pagamento necessário
- `404 Not Found`: Segmento não encontrado

### 📊 Status & Control APIs

#### GET `/streaming/api/status/`
Retorna status completo do sistema de streaming e pagamento.

**Response Example:**
```json
{
  "camera_available": true,
  "camera_status": "online",
  "streaming_status": "active",
  "payment_status": "approved",
  "access_granted": true,
  "message": "✅ Acesso liberado - transmissão ao vivo disponível",
  "stream_url": "/streaming/camera/stream.m3u8",
  "technical_details": {
    "is_streaming": true,
    "process_active": true,
    "playlist_available": true
  }
}
```

**Status Values:**
- `camera_status`: `online` | `offline` | `error` | `unknown`
- `streaming_status`: `active` | `stopped` | `error`  
- `payment_status`: `approved` | `pending` | `failure`

#### POST `/streaming/api/start/`
Inicia o serviço de streaming (requer privilégios admin ou pagamento válido).

**Authorization:** Admin user OR valid payment

**Response Example:**
```json
{
  "success": true,
  "message": "Streaming started successfully",
  "status": {
    "is_streaming": true,
    "camera_status": "online"
  }
}
```

**Responses:**
- `200 OK`: Streaming iniciado/já ativo
- `403 Forbidden`: Sem autorização
- `500 Internal Server Error`: Falha ao iniciar

#### POST `/streaming/api/stop/`
Para o serviço de streaming (requer privilégios admin).

**Authorization:** Admin user only

**Response Example:**
```json
{
  "success": true,
  "message": "Streaming stopped successfully",
  "status": {
    "is_streaming": false
  }
}
```

#### GET `/streaming/api/health/`
Health check para monitoramento de sistema.

**Response Example:**
```json
{
  "healthy": true,
  "timestamp": "1697123456.789",
  "services": {
    "camera": {
      "camera_status": "online",
      "is_streaming": true,
      "process_active": true
    },
    "payment": {
      "service_available": true,
      "cache_available": true
    }
  }
}
```

**Responses:**
- `200 OK`: Sistema saudável
- `503 Service Unavailable`: Sistema com problemas

### 💳 Payment Integration (Existing)

#### POST `/create-payment/`
Cria pagamento MercadoPago (endpoint existente).

#### GET `/check-payment/`
Verifica status do pagamento (endpoint existente).

## 🔧 Códigos de Erro

| Código | Descrição | Ação |
|--------|-----------|------|
| 200 | Sucesso | Continuar operação |
| 403 | Pagamento necessário | Redirecionar para pagamento |
| 404 | Recurso não encontrado | Verificar URL/disponibilidade |
| 500 | Erro interno | Verificar logs/sistema |
| 503 | Serviço indisponível | Aguardar ou verificar câmera |

## 🎯 Fluxos de Integração

### Fluxo Completo do Cliente
```javascript
// 1. Verificar status
const status = await fetch('/streaming/api/status/').then(r => r.json());

if (!status.access_granted) {
  if (status.payment_status !== 'approved') {
    // Redirecionar para pagamento
    window.location.href = '/create-payment/';
  } else {
    // Câmera indisponível
    showMessage(status.message);
  }
} else {
  // Iniciar player HLS
  const video = document.getElementById('videoPlayer');
  if (Hls.isSupported()) {
    const hls = new Hls();
    hls.loadSource(status.stream_url);
    hls.attachMedia(video);
  }
}
```

### Monitoramento de Status
```javascript
// Polling de status (recomendado: 10-30s)
setInterval(async () => {
  const status = await fetch('/streaming/api/status/').then(r => r.json());
  updateUI(status);
}, 15000);
```

## 🔒 Autenticação e Segurança

### Validação de Pagamento
A validação de pagamento é feita via cache do Django:
```python
payment_status = cache.get("payment_status", "pending")
access_granted = payment_status == "approved"
```

### Controles de Segurança
- ✅ Path traversal protection nos segmentos
- ✅ File type validation (.ts only)
- ✅ CORS headers configurados
- ✅ Rate limiting via Django middleware

### Headers de Segurança
```
Access-Control-Allow-Origin: *
Cache-Control: no-cache (playlist) | public, max-age=3600 (segments)
Content-Security-Policy: default-src 'self'
```

## 📱 Compatibilidade

### Browsers Suportados
- ✅ Chrome 80+
- ✅ Firefox 75+  
- ✅ Safari 13+
- ✅ Edge 80+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

### Protocolos
- **HLS (HTTP Live Streaming)**: Protocolo principal
- **RTSP**: Input da câmera (interno)
- **WebRTC**: Futuro (baixa latência)

## 🧪 Testes da API

### Teste Manual com cURL

```bash
# Status sem pagamento
curl -i http://localhost:8000/streaming/api/status/

# Simular pagamento aprovado
curl -X POST http://localhost:8000/webhook/ -H "Content-Type: application/json" \
  -d '{"action": "payment.created"}'

# Verificar acesso liberado  
curl -i http://localhost:8000/streaming/api/status/

# Tentar acessar stream
curl -i http://localhost:8000/streaming/camera/stream.m3u8
```

### Teste com Postman Collection

```json
{
  "info": {"name": "ClimacoCAL Streaming API"},
  "item": [
    {
      "name": "Camera Status",
      "request": {
        "method": "GET",
        "url": "{{baseUrl}}/streaming/api/status/"
      }
    },
    {
      "name": "Start Streaming",
      "request": {
        "method": "POST", 
        "url": "{{baseUrl}}/streaming/api/start/"
      }
    }
  ]
}
```

## 📊 Monitoramento e Métricas

### Métricas Recomendadas
- **Latência de streaming**: Tempo entre RTSP input e HLS output
- **Taxa de erro 5xx**: Disponibilidade do serviço
- **Requests por minuto**: Load balancing
- **Status de pagamento**: Conversão e rejeições

### Logs Estruturados
```python
# Exemplo de logs
logger.info("Served HLS playlist", extra={
  "user_ip": request.META.get('REMOTE_ADDR'),
  "payment_status": "approved",
  "camera_status": "online"
})
```

### Alertas Sugeridos
- 🚨 Camera offline > 5 minutos
- 🚨 FFmpeg process crashed
- 🚨 Error rate > 5%
- ⚠️ Payment failures > 10%

---

## 🚀 Quick Start

1. **Verificar dependências:**
   ```bash
   # FFmpeg instalado
   ffmpeg -version
   
   # Django + streaming app
   python manage.py check streaming
   ```

2. **Iniciar streaming:**
   ```bash
   python manage.py start_camera_streaming --test-camera
   ```

3. **Testar API:**
   ```bash
   curl localhost:8000/streaming/api/health/
   ```

4. **Integrar frontend:**
   ```javascript
   fetch('/streaming/api/status/')
     .then(r => r.json())
     .then(status => console.log(status));
   ```

**📖 Para documentação completa, veja `STREAMING_IMPLEMENTATION_GUIDE.md`**