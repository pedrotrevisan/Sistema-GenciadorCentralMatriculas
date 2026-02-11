@echo off
chcp 65001 >nul
title SYNAPSE - Sistema Central de Matrículas

echo.
echo ============================================================
echo 🚀 SYNAPSE - Iniciando Sistema
echo ============================================================
echo.

REM Verificar se setup foi executado
if not exist "data" (
    echo ⚠️  Diretório 'data' não encontrado!
    echo    Execute setup.bat primeiro
    pause
    exit /b 1
)

echo 📋 Iniciando serviços...
echo.
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo    API Docs: http://localhost:8000/docs
echo.
echo ⚠️  Para parar: Pressione Ctrl+C em cada janela
echo.

REM Iniciar backend em nova janela
start "SYNAPSE Backend" cmd /k "cd backend && uvicorn server:app --reload --host 0.0.0.0 --port 8000"

REM Aguardar 3 segundos
timeout /t 3 /nobreak >nul

REM Iniciar frontend em nova janela
start "SYNAPSE Frontend" cmd /k "cd frontend && yarn dev"

echo.
echo ✅ Serviços iniciados!
echo.
echo 👤 Credenciais padrão:
echo    Admin: admin@senai.br / admin123
echo.
pause
