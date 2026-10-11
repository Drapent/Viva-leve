@echo off
title VivaLeve - Gerador e Instalador Mobile (APK / PWA)
echo ========================================================
echo        VIVALEVE - INSTALADOR DO APK ANDROID PRONTO
echo ========================================================
echo.

set APK_PATH=%~dp0frontend\downloads\VivaLeve.apk

if exist "%APK_PATH%" (
    echo [SUCESSO] O arquivo APK esta pronto para uso:
    echo   Local: %APK_PATH%
    echo.
    echo 1. Abrir a pasta com o arquivo VivaLeve.apk
    echo 2. Instalar diretamente via cabo USB (ADB)
    echo 3. Sair
    echo.
    set /p opcao="Escolha uma opcao (1, 2 ou 3): "

    if "%opcao%"=="1" (
        explorer.exe /select,"%APK_PATH%"
    )
    if "%opcao%"=="2" (
        echo.
        echo Tentando instalar via ADB no celular conectado...
        adb install -r "%APK_PATH%"
        pause
    )
) else (
    echo [AVISO] O arquivo VivaLeve.apk nao foi encontrado.
    echo Baixe diretamente na interface web clicando no botao "Baixar APK".
    pause
)

