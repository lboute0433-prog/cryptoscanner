@echo off
chcp 65001 >nul
title CryptoScanner Pro V11
color 0A

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║       ◈  CryptoScanner Pro V11                  ║
echo  ║  Crypto · Forex · Indices · Multi-Exchange       ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM Charger le fichier .env si présent
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (`findstr /v "^#" .env`) do (
        if not "%%A"=="" if not "%%B"=="" set "%%A=%%B"
    )
    echo  [OK] Configuration .env chargee
) else (
    echo  [INFO] Pas de fichier .env - utilisation des valeurs par defaut
    REM Variables Telegram - modifie ici si pas de .env
    set TG_TOKEN=
    set TG_CHAT=
)

if "%REPORT_HOUR%"=="" set REPORT_HOUR=8
if "%PORT%"=="" set PORT=5000
if "%RUN_BACKGROUND_JOBS%"=="" set RUN_BACKGROUND_JOBS=true

echo  Port: %PORT%
echo  Background jobs: %RUN_BACKGROUND_JOBS%
echo.

REM Recuperer IP locale
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "169.254"') do (
    set LOCAL_IP=%%A
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP: =%

echo  ┌─────────────────────────────────────────────┐
echo  │  PC      : http://localhost:%PORT%            │
if not "%LOCAL_IP%"=="" echo  │  Mobile  : http://%LOCAL_IP%:%PORT%    │
echo  │  Admin   : http://localhost:%PORT%/admin      │
echo  └─────────────────────────────────────────────┘
echo.
echo  Demarrage... (Ctrl+C pour arreter)
echo.

python app.py

if errorlevel 1 (
    echo.
    echo  [ERREUR] L'application s'est arretee.
    echo  Lance installer.bat pour reinstaller les dependances.
    pause
)
