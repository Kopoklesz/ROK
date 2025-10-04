@echo off
REM ROK Auto Farm Manager - Gyors Indító
echo ============================================================
echo   ROK AUTO FARM MANAGER
echo ============================================================
echo.

REM Ellenőrzés: Python telepítve van-e
python --version >nul 2>&1
if errorlevel 1 (
    echo [HIBA] Python nincs telepitve!
    echo Telepitsd innen: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Ellenőrzés: config fájlok léteznek-e
if not exist "config\settings.json" (
    echo [FIGYELEM] Nincs konfiguráció!
    echo.
    echo Futtasd először a setup wizardot:
    echo   python setup_wizard.py
    echo.
    pause
    exit /b 1
)

REM Farm Manager indítása
echo [INFO] Farm Manager inditasa...
echo.
python farm_manager.py

REM Hibakezelés
if errorlevel 1 (
    echo.
    echo [HIBA] A program hibával zárult!
    echo Ellenőrizd a hibaüzeneteket fentebb.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Program befejezve
echo ============================================================
pause