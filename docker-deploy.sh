#!/bin/bash

echo "🚀 Deploy ClimaCocal - Versão Consolidada"
echo "========================================"

# 1. Verificar se arquivo único existe
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Erro: docker-compose.yml não encontrado"
    exit 1
fi

if [ -f "docker-compose-fixed.yml" ]; then
    echo "⚠️  Arquivo duplicado encontrado! Removendo..."
    rm docker-compose-fixed.yml
fi

echo "✅ Arquivo único docker-compose.yml confirmado"

# 2. Criar diretórios necessários
echo "📁 Criando diretórios necessários..."
mkdir -p camera_stream
mkdir -p logs

# 3. Verificar sintaxe
echo "🔍 Validando sintaxe docker-compose..."
docker-compose config --quiet
if [ $? -ne 0 ]; then
    echo "❌ Erro na sintaxe do docker-compose.yml"
    exit 1
fi
echo "✅ Sintaxe válida"

# 4. Parar containers antigos
echo "⏹️  Parando containers antigos..."
docker-compose down

# 5. Rebuild com FFmpeg
echo "🔨 Rebuilding containers..."
docker-compose build --no-cache climacocal

# 6. Subir serviços
echo "🚀 Subindo serviços..."
docker-compose up -d

# 7. Aguardar inicialização
echo "⏳ Aguardando inicialização..."
sleep 10

# 8. Verificar status
echo "📊 Status dos containers:"
docker-compose ps

# 9. Testar conexões
echo "🧪 Testando conexões básicas..."
curl -s -o /dev/null -w "Django: %{http_code}\n" http://localhost:8000/ || echo "Django: OFFLINE"

echo ""
echo "✅ Deploy consolidado completado!"
echo "📁 Agora você tem apenas um arquivo: docker-compose.yml"
echo "🎯 YouTube removido, FFmpeg integrado, volumes corrigidos"