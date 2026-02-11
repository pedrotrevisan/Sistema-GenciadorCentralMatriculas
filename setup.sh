#!/bin/bash

echo ""
echo "============================================================"
echo "🚀 SYNAPSE - Setup Automático (Linux/Mac)"
echo "   Sistema Central de Matrículas SENAI CIMATEC"
echo "============================================================"
echo ""

# Executar script Python de setup
python3 setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erro durante o setup!"
    exit 1
fi

echo ""
echo "✅ Setup concluído!"
