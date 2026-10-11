@echo off
title VivaLeve - Nutricao, Dia do Lixo e Restaurantes
echo ========================================================
echo         INICIANDO O APLICATIVO VIVALEVE
echo ========================================================
echo.

cd /d "%~dp0"

REM Verificar se o ambiente virtual existe
if not exist ".venv" (
    echo [INFO] Criando ambiente virtual...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [INFO] Instalando dependencias...
    pip install -r requirements.txt
    python backend/seed_foods.py
    python backend/seed_restaurants.py
)

REM Executar inicializador Python
.\.venv\Scripts\python.exe iniciar_app.py

if %errorlevel% neq 0 (
    echo.
    echo Ocorreu um erro ao executar o aplicativo.
    pause
)
