@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo 🚀 SYNAPSE - Setup Automático (Windows)
echo    Sistema Central de Matrículas SENAI CIMATEC
echo ============================================================
echo.

REM Executar script Python de setup
python setup.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Erro durante o setup!
    pause
    exit /b 1
)

echo.
echo ✅ Setup concluído! Pressione qualquer tecla para fechar...
pause >nul
