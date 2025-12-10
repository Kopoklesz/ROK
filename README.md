# ⚡ Gyors Start Útmutató

## 1️⃣ Telepítés (5 perc)

### A) Python csomagok telepítése

```bash
pip install -r requirements.txt
```

### B) Tesseract OCR telepítése

1. Töltsd le: https://github.com/UB-Mannheim/tesseract/wiki
2. Telepítsd (alapértelmezett hely: `C:\Program Files\Tesseract-OCR`)
3. Nyisd meg a `library.py` fájlt
4. Módosítsd az útvonalat (30. sor):

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### C) 🤖 EasyOCR telepítése (OPCIONÁLIS - ML-alapú OCR)

**Miért?** Jobb OCR pontosság, különösen éjszaka! Neural network alapú felismerés.

```bash
pip install easyocr
```

**Előnyök:**
- ✅ Jobb OCR pontosság éjjel/nappal (neural network)
- ✅ Kevesebb OCR hiba → kevesebb retry loop
- ✅ **Gyorsabb összesített futás** (kevesebb 5-60 perc várakozás)
- ✅ Automatikus fallback Tesseract-ra

**Hátrányok:**
- ⚠️  Egy OCR hívás lassabb (1-2 sec vs 0.1 sec)
- ⚠️  Első indítás: model letöltése (~500MB)
- ⚠️  Több memória használat

**Miért gyorsabb összességében?**
- Tesseract éjjel: OCR hiba → retry → 5 min várakozás → újra hiba... = **órák veszteség**
- EasyOCR éjjel: 1.5 sec → **sikeres OCR elsőre** → folytatja a munkát

**Teszt:** `setup_wizard.py` → 9. Advanced Tools → 3. Test EasyOCR vs Tesseract

### D) Játék ablak nevének beállítása

Nyisd meg a `library.py` fájlt, és módosítsd a 33. sort:

```python
game_window_title = "BlueStacks"  # <-- Cseréld le a saját emulátorodra!
```

**Gyakori nevek:**
- BlueStacks → `"BlueStacks"`
- NoxPlayer → `"NoxPlayer"`
- LDPlayer → `"LDPlayer"`
- MEmu → `"MEmu"`

---

## 2️⃣ Első Konfiguráció (10 perc)

### Indítsd el a játékot, majd:

```bash
python setup_wizard.py
```

### A varázsló 5 lépésben végigvezet:

1. **Erőforrás számlálók** - Jelöld ki a búza, fa, kő, arany számokat
2. **Idő régiók** - Jelöld ki az időket (march + gather)
3. **Farm koordináták** - Kattints a térképre, farmokra, gombokra
4. **Gather gomb** - Jelöld ki a Gather gombot
5. **Beállítások** - Automatikusan létrejön

**Tipp:** Ha egy erőforrást nem akarsz használni (pl. csak búza + fa), nyomd meg az ESC-et annál a lépésnél.

---

## 3️⃣ Futtatás

### Indítsd el a játékot, majd:

```bash
python farm_manager.py
```

### Mit csinál?

1. ⏰ **20-25 mp várakozás** - Átválthatsz a játékra
2. 📊 **Erőforrások kiolvasása** - OCR-rel beolvassa a számokat
3. 🧮 **Kiválasztás** - Legkevesebb erőforrást választja (osztva: búza/fa÷4, kő÷3, arany÷2)
4. 🌾 **Farm küldés** - 4x lefuttatja a farm ciklust
5. ⏳ **Várakozás** - Max időig vár, majd újrakezdi

### Leállítás: **CTRL+C**

---

## 🔧 Gyors Beállítások

Szerkeszd a `config/settings.json` fájlt:

```json
{
  "repeat_count": 4,      // Hányszor ismétli egy ciklusban (4x farm)
  "max_cycles": 100,      // Max ciklusok száma (100x farm küldés)
  "human_wait_min": 3,    // Min várakozás kattintások között
  "human_wait_max": 8     // Max várakozás kattintások között
}
```

---

## 🆘 Gyors Hibakeresés

### ❌ "Játék ablak nem található"

→ Módosítsd a `library.py` 33. sorát a játék ablak nevére

### ❌ "Gather gomb nem található"

→ Futtasd újra: `python setup_wizard.py` és jelöld ki újra a Gather gombot

### ❌ "OCR nem olvassa az értékeket"

→ Ellenőrizd Tesseract telepítését, futtasd újra a setup wizardot

### ❌ "Rossz helyre kattint"

→ Futtasd: `python utils/coordinate_helper.py` és nézd meg a koordinátákat

---

## 📝 Hasznos Parancsok

```bash
# Setup újrafuttatása
python setup_wizard.py

# Koordináták ellenőrzése
python utils/coordinate_helper.py

# Régió teszt
python utils/region_selector.py

# Normál futtatás
python farm_manager.py
```

---

## ✅ Checklist - Első Használat

- [ ] Python csomagok telepítve (`pip install -r requirements.txt`)
- [ ] Tesseract OCR telepítve és beállítva
- [ ] Játék ablak neve beállítva (`library.py`)
- [ ] Setup wizard lefuttatva (`python setup_wizard.py`)
- [ ] Minden régió és koordináta beállítva
- [ ] Tesztfuttatás sikeres (`python farm_manager.py`)

---

## 🚀 ML-Enhanced Features (ÚJ v2.1)

### Advanced Tools Menu

```bash
python setup_wizard.py
# Válaszd: 9. Advanced Tools
```

#### 1️⃣ Template Capture - Gomb mentése
- Koordinátából készít template-et
- Használd ha ablak méret változik
- Batch capture: mind a 4 training gomb egyszerre

#### 2️⃣ Test Template Matching
- Template keresése a képernyőn
- Multi-scale támogatás
- Threshold beállítás

#### 3️⃣ EasyOCR vs Tesseract Teszt
- ML vs pattern-matching OCR
- Élő teszt összehasonlítás
- Debug save (logs/ocr_debug/)

#### 4️⃣ Test & Verify Menu
- Config validálás
- Koordináta vizualizáció
- OCR régió vizualizáció
- Module-specific testing (Training/Gathering/Explorer)

**Részletes dokumentáció:** `tools/README.md`

---

**Ha minden kész, jó farmolást!** 🌾🚜

---

## 📋 Roadmap & Változások

### ✅ Kész (v2.1 ML-Enhanced)
- EasyOCR támogatás (ML-alapú OCR)
- Enhanced template matching (multi-scale)
- Button template capture tool
- Advanced Tools menu
- OCR comparison tool
- Batch template capture

### ✅ Kész (v2.0)
- Module-specific testing
- Config validator + visualizer
- Progressive retry logic
- ESC + 2x SPACE clean state
- OCR preprocessing (OTSU, Adaptive, CLAHE)

### 🔜 Tervezett
- Szövetségi rally csatlakozás
- Szövetségi rally indítás
- Fő épület fejlesztés
- Relatív koordináták (%-os)
- Hybrid mode (koordináta + template fallback)
- Web UI config editor 
