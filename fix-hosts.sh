#!/bin/bash

echo "🔧 Script para corrigir acesso local ao climacocal.rosa.local"
echo "============================================================"

echo "1. Adicionando domínio ao hosts file..."
echo "Execute este comando como administrador:"
echo ""
echo "echo '127.0.0.1 climacocal.rosa.local' | sudo tee -a /etc/hosts"
echo ""
echo "Ou adicione manualmente ao arquivo /etc/hosts:"
echo "127.0.0.1 climacocal.rosa.local"
echo ""

echo "2. Verificando se foi adicionado:"
echo "cat /etc/hosts | grep climacocal"
echo ""

echo "3. Após adicionar, teste no navegador:"
echo "http://climacocal.rosa.local/"
echo ""

echo "IMPORTANTE: Execute o comando sudo manualmente no terminal!"