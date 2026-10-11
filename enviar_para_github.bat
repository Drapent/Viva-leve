@echo off
title VivaLeve - Enviar para GitHub (Deploy Render.com)
echo ========================================================
echo       ENVIAR VIVALEVE PARA O GITHUB (RENDER.COM)
echo ========================================================
echo.
set /p REPO_URL="Cole a URL do seu repositorio no GitHub (ex: https://github.com/seu-usuario/vivaleve.git): "
if "%REPO_URL%"=="" (
    echo Nenhuma URL informada. Operacao cancelada.
    pause
    exit /b
)

"C:\Users\kiqlo\.gemini\antigravity\scratch\mingit\cmd\git.exe" remote remove origin 2>nul
"C:\Users\kiqlo\.gemini\antigravity\scratch\mingit\cmd\git.exe" remote add origin %REPO_URL%
"C:\Users\kiqlo\.gemini\antigravity\scratch\mingit\cmd\git.exe" push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   SUCESSO! O codigo foi enviado para o seu GitHub!
    echo   Agora acesse https://dashboard.render.com e crie o servico.
    echo ========================================================
) else (
    echo.
    echo Ocorreu um erro ao enviar. Verifique se o repositorio existe e suas permissoes.
)
pause
