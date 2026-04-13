@echo off
title CryptoScanner Pro V2 - Installation
echo.
echo ================================================
echo   CryptoScanner Pro V2 - Installation
echo ================================================
echo.

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python non detecte !
    echo Telecharge : https://www.python.org/downloads/
    echo Coche "Add Python to PATH" !
    pause & exit /b 1
)

echo [OK] Python detecte
echo.
echo Installation des dependances...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo ================================================
echo   Installation terminee !
echo   Lance lancer.bat pour demarrer
echo ================================================
pause
