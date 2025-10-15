#!/bin/bash
set -e

echo "=========================================="
echo "ClimaCocal Camera Streamer Container"
echo "=========================================="

# Gerar imagem offline se não existir
if [ ! -f "/camera/static/offline.png" ]; then
    echo "Gerando imagem offline..."
    cd /camera/scripts
    python3 generate_offline_image.py
fi

# Exibir configurações (sem senhas)
echo "Configurações:"
echo "- Câmera IP: $(echo $CAMERA_RTSP_URL | sed 's/.*@\([^:]*\):.*/\1/')"
echo "- YouTube RTMP: $YOUTUBE_RTMP_URL"
echo "- Resolução: $STREAM_RESOLUTION"
echo "- FPS: $STREAM_FPS"
echo "- Bitrate: $STREAM_BITRATE"
echo "- Health Check: ${HEALTH_CHECK_INTERVAL}s"
echo "- Fallback: $ENABLE_FALLBACK"

# Verificar dependências
echo "Verificando dependências..."
ffmpeg -version >/dev/null 2>&1 && echo "✅ FFmpeg disponível" || echo "❌ FFmpeg não encontrado"
ffprobe -version >/dev/null 2>&1 && echo "✅ FFprobe disponível" || echo "❌ FFprobe não encontrado"
ping -c 1 google.com >/dev/null 2>&1 && echo "✅ Conectividade OK" || echo "⚠️ Sem conectividade externa"

# Testar conectividade com a câmera
CAMERA_IP=$(echo $CAMERA_RTSP_URL | sed 's/.*@\([^:]*\):.*/\1/')
echo "Testando conectividade com câmera ($CAMERA_IP)..."
if ping -c 1 -W 3 $CAMERA_IP >/dev/null 2>&1; then
    echo "✅ Câmera acessível"
else
    echo "⚠️ Câmera não responde ao ping"
fi

# Iniciar dashboard Flask em background
echo "Iniciando dashboard Flask..."
cd /camera/scripts
python3 dashboard.py &
FLASK_PID=$!

# Aguardar um pouco para Flask inicializar
sleep 3

# Verificar se Flask está rodando
if kill -0 $FLASK_PID 2>/dev/null; then
    echo "✅ Dashboard Flask rodando na porta 8001"
else
    echo "❌ Erro ao iniciar dashboard Flask"
    exit 1
fi

echo "=========================================="
echo "🎬 Sistema iniciado com sucesso!"
echo "Dashboard: http://localhost:8001"
echo "=========================================="

# Manter container rodando e monitorar Flask
while kill -0 $FLASK_PID 2>/dev/null; do
    sleep 30
done

echo "❌ Dashboard Flask parou, encerrando container"
exit 1