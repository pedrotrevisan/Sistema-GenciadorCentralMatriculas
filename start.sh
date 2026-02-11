#!/bin/bash

echo ""
echo "============================================================"
echo "🚀 SYNAPSE - Iniciando Sistema"
echo "============================================================"
echo ""

# Verificar se setup foi executado
if [ ! -d "data" ]; then
    echo "⚠️  Diretório 'data' não encontrado!"
    echo "   Execute ./setup.sh primeiro"
    exit 1
fi

echo "📋 Iniciando serviços..."
echo ""
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "⚠️  Para parar: Pressione Ctrl+C"
echo ""

# Função para cleanup
cleanup() {
    echo "\n\n🛑 Parando serviços..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Iniciar backend em background
cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

echo "✅ Backend iniciado (PID: $BACKEND_PID)"

# Aguardar 3 segundos
sleep 3

# Iniciar frontend em background
cd frontend
yarn dev &
FRONTEND_PID=$!
cd ..

echo "✅ Frontend iniciado (PID: $FRONTEND_PID)"
echo ""
echo "✅ Sistema rodando!"
echo ""
echo "👤 Credenciais padrão:"
echo "   Admin: admin@senai.br / admin123"
echo ""

# Aguardar indefinidamente
wait
