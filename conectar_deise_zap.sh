#!/bin/bash
# ==============================================================================
# Script de Inicialização da Agente DEISE (WhatsApp Designtex Tecidos)
# Executa na VPS onde roda o conexo.dev
# ==============================================================================

set -e

echo "🚀 Iniciando os serviços do CONEXO e Evolution API (WhatsApp)..."
docker compose up -d

echo "⏳ Aguardando a Evolution API inicializar (10 segundos)..."
sleep 10

API_KEY="conexo_deise_secret_2026"
BASE_URL="http://127.0.0.1:8080"

echo "📱 Criando/Verificando a instância 'deise' para o número +55 31 99015-1359..."
curl -s -X POST "$BASE_URL/instance/create" \
  -H "Content-Type: application/json" \
  -H "apikey: $API_KEY" \
  -d '{
    "instanceName": "deise",
    "token": "deise_secret_token",
    "number": "5531990151359",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }' > /dev/null || true

echo ""
echo "=============================================================================="
echo "           QR CODE DE CONEXÃO DA DEISE (WHATSAPP BUSINESS)"
echo "=============================================================================="
echo "Abra o WhatsApp Business no celular:"
echo "1. Toque nos 3 pontinhos (ou Ajustes) -> Aparelhos Conectados"
echo "2. Toque em 'Conectar um aparelho'"
echo "3. Aponte a câmera para o QR Code abaixo ou abra a URL de conexão:"
echo ""
echo "🔗 URL DIRETA PARA VISUALIZAR O QR CODE NO NAVEGADOR:"
echo "https://conexo.dev/evolution/instance/connect/deise"
echo "=============================================================================="
echo ""

# Busca o QR code em formato texto caso o terminal suporte
curl -s -X GET "$BASE_URL/instance/connect/deise" \
  -H "apikey: $API_KEY" | grep -o '"code":"[^"]*"' || true

echo ""
echo "✅ Quando a leitura for concluída, a Deise estará 100% ativa no WhatsApp!"
