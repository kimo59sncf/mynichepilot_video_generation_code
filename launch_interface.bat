@echo off
setlocal EnableExtensions
chcp 65001 >nul
title MyNichePilot - Studio VIP
cd /d "%~dp0"

set "PORT=8000"
if not "%~1"=="" set "PORT=%~1"

echo ============================================================
echo    MyNichePilot - Interface VIP (Studio de Production)
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERREUR] Python 3 introuvable dans le PATH.
    echo          Installez Python 3.10+ puis relancez ce script.
    pause
    exit /b 1
)

rem Verifie / installe les dependances
python -c "import PIL, numpy, scipy, edge_tts" >nul 2>nul
if errorlevel 1 (
    echo [INFO] Installation des dependances Python depuis requirements.txt...
    python -m pip install -r requirements.txt
    echo.
)

echo [OK]   Demarrage du serveur sur http://127.0.0.1:%PORT%
echo [OK]   Arret du serveur : Ctrl+C dans cette fenetre.
echo.

rem Ouvre le navigateur apres un court delai (temps d'initialisation du serveur)
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:%PORT%'"

python server.py --port %PORT%

pause