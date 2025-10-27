#!/bin/bash
# Script simples para iniciar streaming RTSP para HLS

# Configurações
RTSP_URL="rtsp://admin:CoraRosa@192.168.3.62:554/cam/realmonitor?channel=1&subtype=0"
OUTPUT_DIR="/home/bruno/cocalClima/camera_stream"
PLAYLIST_FILE="$OUTPUT_DIR/stream.m3u8"

# Criar diretório se não existir
mkdir -p "$OUTPUT_DIR"

# Limpar arquivos antigos
rm -f "$OUTPUT_DIR"/*.ts "$OUTPUT_DIR"/*.m3u8

echo "Iniciando streaming RTSP para HLS..."
echo "RTSP URL: $RTSP_URL"
echo "Output: $OUTPUT_DIR"

# Comando FFmpeg simplificado
ffmpeg -i "$RTSP_URL" \
    -c:v libx264 -preset ultrafast -tune zerolatency \
    -c:a aac -b:a 128k \
    -f hls \
    -hls_time 3 \
    -hls_list_size 10 \
    -hls_flags delete_segments+independent_segments \
    -hls_segment_filename "$OUTPUT_DIR/segment_%03d.ts" \
    "$PLAYLIST_FILE" &

echo "Streaming iniciado em background (PID: $!)"
echo "Playlist disponível em: $PLAYLIST_FILE"