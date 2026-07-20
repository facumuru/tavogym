@echo off
echo ========================================
echo   TAVOGYM - Iniciando servidor
echo ========================================
echo.

cd /d "%~dp0"

if not exist "database.db" (
    echo Primera ejecucion - preparando...
    python generate_icons.py
)

echo Servidor en: http://localhost:5000
echo Admin: tavo / tavogym2024
echo.
echo Para acceder desde el celular, usa la IP de esta PC:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do echo   http://%%a:5000
echo.
python app.py
pause
