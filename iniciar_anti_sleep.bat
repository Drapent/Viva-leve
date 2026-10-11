@echo off
title VivaLeve - Guardiao Anti-Sleep 24/7
color 0A
chcp 65001 >nul

echo =========================================================
echo       VIVALEVE - INICIANDO GUARDIÃO ANTI-SLEEP 24/7
echo =========================================================
echo Mantendo https://viva-leve.onrender.com sempre acordado...
echo.

cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" anti_sleep.py
) else (
    python anti_sleep.py
)

pause
