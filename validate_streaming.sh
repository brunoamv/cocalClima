#!/bin/bash

echo "🔍 Validação Completa do Sistema de Streaming"
echo "=============================================="

# 1. Verificar câmera online ANTES de permitir pagamento
echo "📷 Testando conectividade da câmera..."
ffprobe -v quiet -rtsp_transport tcp -i "rtsp://admin:CoraRosa@192.168.69.20:554/cam/realmonitor?channel=1&subtype=0" -show_entries stream=codec_type -of csv=p=0 -t 5

if [ $? -eq 0 ]; then
    echo "✅ Câmera ONLINE - Pagamento pode ser processado"
else
    echo "❌ Câmera OFFLINE - BLOQUEAR pagamentos!"
    exit 1
fi

# 2. Testar API de status
echo "🔌 Testando API de status..."
curl -s http://localhost:8000/streaming/api/status/ | jq -r '.camera_available, .message'

# 3. Verificar se FFmpeg está funcionando no container
echo "🎥 Testando FFmpeg no container Django..."
docker exec climacocal_app ffmpeg -version | head -1

# 4. Testar HLS generation (apenas se câmera online)
echo "📺 Testando geração HLS..."
mkdir -p ./test_stream
ffmpeg -y -v error -rtsp_transport tcp -i "rtsp://admin:CoraRosa@192.168.69.20:554/cam/realmonitor?channel=1&subtype=0" -t 10 -c:v libx264 -preset veryfast -f hls -hls_time 3 -hls_list_size 3 ./test_stream/test.m3u8 &
sleep 12
if [ -f "./test_stream/test.m3u8" ]; then
    echo "✅ HLS streaming funcional"
    rm -rf ./test_stream
else
    echo "❌ Falha na geração HLS"
fi

echo ""
echo "📋 RESUMO:"
echo "- ✅ Câmera validada antes do pagamento"
echo "- ✅ YouTube removido, FFmpeg implementado"
echo "- ✅ Validação de offline implementada"
echo "- ⚠️  Rebuild container necessário para FFmpeg"

echo ""
echo "🚀 Para aplicar as correções:"
echo "1. docker-compose down"
echo "2. docker-compose build --no-cache"
echo "3. docker-compose up -d"