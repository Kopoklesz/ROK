#!/bin/bash
# ROK Auto Farm Manager - Gyors Indító (Linux/Mac)

echo "============================================================"
echo "  ROK AUTO FARM MANAGER"
echo "============================================================"
echo ""

# Python ellenőrzés
if ! command -v python3 &> /dev/null; then
    echo "[HIBA] Python nincs telepítve!"
    exit 1
fi

# Config ellenőrzés
if [ ! -f "config/settings.json" ]; then
    echo "[FIGYELEM] Nincs konfiguráció!"
    echo ""
    echo "Futtasd először a setup wizardot:"
    echo "  python3 setup_wizard.py"
    echo ""
    exit 1
fi

# Farm Manager indítása
echo "[INFO] Farm Manager indítása..."
echo ""
python3 farm_manager.py

# Hibakezelés
if [ $? -ne 0 ]; then
    echo ""
    echo "[HIBA] A program hibával zárult!"
    exit 1
fi

echo ""
echo "============================================================"
echo "  Program befejezve"
echo "============================================================"