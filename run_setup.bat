@echo off
REM ROK Auto Farm Manager - Setup Wizard Indító
echo ============================================================
echo   ROK AUTO FARM MANAGER - SETUP WIZARD
echo ============================================================
echo.

REM Python ellenőrzés
python --version >nul 2>&1
if errorlevel 1 (
    echo [HIBA] Python nincs telepitve!
    pause
    exit /b 1
)

REM Játék figyelmeztetés
echo [INFO] Indítsd el a játékot mielőtt folytatod!
echo.
pause

REM Setup futtatása
python setup_wizard.py

if errorlevel 1 (
    echo.
    echo [HIBA] Setup sikertelen!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Setup befejezve!
echo   Most már futtathatod: run_farm.bat
echo ============================================================
pause