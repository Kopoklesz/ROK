# ROK Auto Farm - Tools & Validation

## 📋 Rendszer Struktúra

```
ROK/
├── farm_manager.py          # Fő orchestrator (Queue + Timer hurok)
├── setup_wizard.py          # Interaktív setup + TEST mód
├── config/                  # JSON konfigok
│   ├── settings.json
│   ├── training_coords.json
│   ├── training_time_regions.json
│   ├── gathering_coords.json
│   ├── resource_regions.json
│   └── ...
├── managers/                # Feature managers
│   ├── training_manager.py
│   ├── gathering_manager.py
│   ├── alliance_manager.py
│   └── ...
├── utils/                   # Utility modulok
│   ├── queue_manager.py     # FIFO task queue
│   ├── timer_manager.py     # Deadline-alapú timer
│   ├── scheduler.py         # Cron-szerű ütemezés
│   └── logger.py
├── farms/                   # Farm típusok
│   ├── base_farm.py
│   ├── wheat_farm.py
│   └── ...
└── tools/                   # Test & validation eszközök
    ├── config_validator.py  # Config vizualizáló/ellenőrző
    └── README.md            # Ez a fájl
```

---

## 🛠️ Test Tools

### 1. Config Validator

**Config ellenőrzés + vizualizáció**

#### Használat

#### 1. **Összes teszt futtatása**
```bash
python tools/config_validator.py --mode all
```

Eredmény:
- `logs/config_visualization.png` - Koordináták a képernyőn
- `logs/ocr_regions_visualization.png` - OCR régiók a képernyőn
- Konzol: OCR élő teszt eredmények

#### 2. **Csak config ellenőrzés**
```bash
python tools/config_validator.py --mode check
```

Ellenőrzi:
- ✅ Minden szükséges config fájl létezik-e
- ✅ Minden koordináta/régió be van-e állítva
- ⚠️ Hiányzó értékek listája

#### 3. **Koordináta vizualizáció**
```bash
python tools/config_validator.py --mode visual-coords --type all
```

Típusok: `training`, `gathering`, `alliance`, `all`

Eredmény:
- Keresztekkel + címkékkel jelöli a koordinátákat
- Színek:
  - 🔴 Piros: Training panel/gombok
  - 🔵 Kék: Barracks
  - 🟢 Zöld: Archery
  - 🟣 Lila: Stable
  - 🟠 Narancs: Siege
  - 🔷 Cyan: Gathering (map, search)
  - 🟡 Sárga: Alliance

#### 4. **OCR régió vizualizáció**
```bash
python tools/config_validator.py --mode visual-ocr --type all
```

Típusok: `training`, `resource`, `gathering`, `all`

Eredmény:
- Téglalapokkal jelöli az OCR régiókat
- Színek:
  - 🔴 Piros: Training time régiók
  - 🟢 Zöld: Resource régiók

#### 5. **OCR élő teszt**
```bash
python tools/config_validator.py --mode test-ocr
```

Eredmény:
- Minden OCR régiót beolvas MOST
- Konzolra kiírja az eredményeket
- Látod hogy működik-e az OCR

---

## 🧙 Setup Wizard Test Mód

A wizard-ban (Option 8) elérhető test menü:

```bash
python setup_wizard.py
# Válaszd: 8. Test & Verify
```

### Test Menu opciók:

1. **Validate All Configs**
   - Futtatja: `config_validator.py --mode check`
   - Gyors check: minden config rendben van-e

2. **Visualize Coordinates**
   - Választható típus: Training/Gathering/Alliance/All
   - Screenshot-ot készít + rájeleníti a koordinátákat
   - Eredmény: `logs/config_visualization.png`

3. **Visualize OCR Regions**
   - Választható típus: Training/Resource/Gathering/All
   - Screenshot-ot készít + rájeleníti az OCR régiókat
   - Eredmény: `logs/ocr_regions_visualization.png`

4. **Test OCR Regions (Live)**
   - ÉLŐBEN teszteli az OCR-t
   - Látod hogy mi olvasódik ki

5. **Run Full Test Suite**
   - Mind a 4 teszt egyben
   - Teljes validáció

6. **Test Module (ÚJ!)**
   - Training/Gathering/Explorer modul tesztelése
   - Lépésről-lépésre vizualizáció
   - HTML riport generálás

---

## 🧪 Module Tester - MODUL-SPECIFIKUS TESZTELÉS

### **Mi ez?**

Minden modul (Training/Gathering/Explorer) **teljes folyamatát** végigfuttatja + vizualizálja:
- 📸 Screenshot **minden lépésnél**
- 🖱️ Kattintások **vizualizálva** (kereszt + címke)
- 📖 OCR olvasások **vizualizálva** (téglalap + eredmény)
- 📊 HTML riport **minden lépéssel**
- ❌ Hiba esetén: **pontosan látod hol akadt meg**

### **Használat**

#### **Wizard-ból:**
```bash
python setup_wizard.py
# Válaszd: 8. Test & Verify
# Válaszd: 6. Test Module
# Válaszd a modult: Training/Gathering/Explorer
```

#### **Standalone:**
```bash
# Training teszt
python tools/module_tester.py --module training

# Gathering teszt
python tools/module_tester.py --module gathering

# Explorer teszt
python tools/module_tester.py --module explorer
```

### **Mit csinál?**

#### **Training Module Test:**
1. Config betöltése
2. Training panel megnyitása (vizualizálja a kattintást)
3. Mind a 4 building OCR olvasása (vizualizálja az OCR régiókat + eredményeket)
4. Panel bezárása
5. Clean state (ESC + 2x SPACE)
6. HTML riport generálás

#### **Gathering Module Test:**
1. Config betöltése
2. Resource OCR (wheat/wood/stone/gold) - vizualizálja mind a 4 régiót
3. Map button kattintás
4. Search button kattintás
5. Clean state
6. HTML riport

#### **Explorer Module Test:**
1. Config betöltése
2. Map button kattintás
3. Explore button kattintás
4. Send button kattintás (ha van)
5. Clean state
6. HTML riport

### **Eredmények**

**Fájlok:** `logs/module_tests/{module_name}/`

**1. HTML Riport:** `{timestamp}_report.html`
- Lépésről-lépésre timeline
- Minden screenshot beágyazva
- Kattintások + OCR eredmények
- Hibák kiemelve

**2. Screenshot-ok:** `{timestamp}_step_XXX_*.png`
- `step_001.png` - Általános screenshot
- `step_002_click_Open_Panel.png` - Kattintás vizualizálva
- `step_003_ocr_BARRACKS_Time.png` - OCR vizualizálva
- `step_XXX_ERROR.png` - Hiba screenshot (ha volt)

**3. JSON Log:** `{timestamp}_test_log.json`
- Teljes teszt log strukturáltan
- Minden lépés időbélyeggel
- Programatikus feldolgozáshoz

### **Példa Vizualizáció**

#### **Kattintás screenshot:**
```
🖱️ Piros kereszt + kör a kattintás helyén
📝 Címke: "Open Panel"
```

#### **OCR screenshot:**
```
📖 Zöld téglalap az OCR régió körül
📝 Címke: "BARRACKS Time"
✅ Eredmény a képen: "Result: 'Training 02:15:30'"
```

#### **Hiba screenshot:**
```
❌ Screenshot a hiba pillanatában
📝 Hiba üzenet rá írva
→ Pontosan látod mi volt a képernyőn amikor megakadt
```

### **Mikor használd?**

1. **Új setup ellenőrzésére:**
   ```bash
   # Mindent beállítottál → Teszteld le
   python tools/module_tester.py --module training
   ```

2. **Hibakeresésre:**
   ```
   "Training manager mindig megakad!"
   → Futtasd a training tesztet
   → Nézd meg a HTML riportot
   → Látod melyik lépésnél akad meg
   → Látod mi volt a képernyőn
   ```

3. **Módosítás után ellenőrzésre:**
   ```
   "Átállítottam a koordinátákat"
   → Module teszt
   → Látod működik-e az új setup
   ```

---

## ❓ Koordináta Pontosság - VÁLASZ A KÉRDÉSRE

### "Screenshot koordináták pontosak? Nem csúsznak?"

**Válasz: IGEN, pontosak - HA a következők teljesülnek:**

#### ✅ **Működik (FIX pozíciók):**
- Játék ablak **mindig ugyanakkora**
- Játék ablak **mindig ugyanott van**
- Felbontás **nem változik**
- Windows UI scale **nem változik**

#### ❌ **NEM működik (koordináták csúsznak):**
- Ablak méret változik
- Ablak pozíció változik
- Felbontás változik (pl. 1920x1080 → 2560x1440)
- UI scale változik

### **ELLENŐRZÉS:**

#### 1. **Ablak méret/pozíció check:**
```python
from library import initialize_game_window
initialize_game_window("BlueStacks")
# Ez megkeresi + aktiválja az ablakot
# Ha nem ugyanakkora/ugyanott van → koordináták rossz helyen lesznek
```

#### 2. **Vizualizáció:**
```bash
python tools/config_validator.py --mode visual-coords --type all
```
- Nézd meg a `logs/config_visualization.png` fájlt
- A kereszteknek **pont a gombokra/régiókra** kell mutatni
- Ha nem ott vannak → ablak méret/pozíció változott

#### 3. **OCR régió check:**
```bash
python tools/config_validator.py --mode visual-ocr --type all
```
- Nézd meg a `logs/ocr_regions_visualization.png` fájlt
- A téglalapoknak **pont az OCR területeket** kell körbevenni
- Ha nem jók → ablak méret/pozíció változott

### **MEGOLDÁS HA CSÚSZIK:**

#### Opció 1: **Fix ablak pozíció/méret**
- BlueStacks: Ablak méretét ne változtasd
- BlueStacks: Pozíciót ne változtasd
- → Koordináták FIX maradnak

#### Opció 2: **Újra kalibráció**
```bash
python setup_wizard.py
# Állítsd be újra a koordinátákat/régiókat
```

#### Opció 3: **Relatív koordináták (JÖVŐ)**
- Jelenleg: Abszolút (X, Y) koordináták
- Jövőbeli fejlesztés: Relatív (%) koordináták
- Pl: "45% width, 30% height" → ablak mérettől függetlenül működik

---

## 🔍 Hibaelhárítás

### "Training OCR nem működik"

1. **Vizualizáld a régiókat:**
   ```bash
   python tools/config_validator.py --mode visual-ocr --type training
   ```

2. **Ellenőrzd a képet:**
   - Nyisd meg: `logs/ocr_regions_visualization.png`
   - A piros téglalapok jó helyen vannak?
   - Ha NEM → újra kell kalibrálni

3. **Teszteld élőben:**
   ```bash
   python tools/config_validator.py --mode test-ocr
   ```
   - Látod mi olvasódik ki
   - Ha üres/rossz → régió rosszul van beállítva

### "Gather button nem találja"

1. **Vizualizáld a koordinátákat:**
   ```bash
   python tools/config_validator.py --mode visual-coords --type gathering
   ```

2. **Ellenőrzd a template-et:**
   - `images/Gather.png` létezik?
   - Megfelelő méretű? (kb 50x50 px)

### "Config validálás hibákat dob"

```bash
python tools/config_validator.py --mode check
```
- Minden ❌ hibát javíts
- Minden ⚠️ figyelmeztetést nézz meg

---

## 📊 Queue + Timer Rendszer

### Egyszerűsített működés:

```
┌─────────────┐
│ Timer       │ → Deadline lejár → Task-ot ad Queue-ba
│ Manager     │
└─────────────┘
       ↓
┌─────────────┐
│ Queue       │ → FIFO: Task sorrend
│ Manager     │
└─────────────┘
       ↓
┌─────────────┐
│ farm_manager│ → Kiveszi a következő task-ot
│ main loop   │ → Odaadja a megfelelő manager-nek
└─────────────┘
       ↓
┌─────────────┐
│ Training /  │ → Végrehajtja a task-ot
│ Gathering / │ → Ha sikerült: timer-t ad vissza
│ Alliance    │ → Ha hiba: retry timer-t ad vissza
└─────────────┘
```

**Előnyök:**
- ✅ Egyszerű: 1 hurok mindenhol
- ✅ Időzített: Timer-ek kezelik a deadline-okat
- ✅ Sorrendezett: Queue biztosítja a FIFO-t
- ✅ Karbantartható: Managers függetlenek egymástól

---

## 🚀 Gyors Start

### 1. Setup
```bash
python setup_wizard.py
# Állítsd be a training/gathering/stb koordinátákat
```

### 2. Test
```bash
python setup_wizard.py
# Option 8: Test & Verify
# Option 5: Run Full Test Suite
```

### 3. Ellenőrzés
- Nézd meg: `logs/config_visualization.png`
- Nézd meg: `logs/ocr_regions_visualization.png`
- Konzol: OCR eredmények

### 4. Futtatás
```bash
python farm_manager.py
```

---

## 🤖 ML-Enhanced Features (ÚJ!)

### **EasyOCR - Machine Learning OCR**

**Mi ez?**
- ML-alapú OCR engine (vs. Tesseract pattern-matching)
- Jobb éjszakai felismerés
- Automatikus fallback Tesseract-ra ha EasyOCR nem elérhető

**Telepítés:**
```bash
pip install easyocr
```

**Használat:**
- Automatikus: `library.py` automatikusan EasyOCR-t használ ha elérhető
- Manuális teszt: Wizard → 9. Advanced Tools → 3. Test EasyOCR vs Tesseract

**Előnyök:**
- ✅ **Neural network alapú** - VALÓBAN "megtanulja" a szöveget (pre-trained model)
- ✅ Jobb OCR pontosság éjjel/nappal
- ✅ Kevesebb OCR hiba → **kevesebb retry → gyorsabb összesítve**
- ✅ Kevesebb preprocessing szükséges

**Hátrányok:**
- ⚠️  Egy OCR hívás lassabb (1-2 sec vs 0.1 sec)
- ⚠️  Több memória (~500MB model)

**Fontos:** Bár egy OCR hívás lassabb, a teljes folyamat gyorsabb, mert nem ragad el retry loop-okban!

---

### **Template Matching - Dinamikus Gomb Keresés**

**Mi ez?**
- OpenCV-alapú képfelismerés (**NEM ML/AI** - egyszerű képillesztés!)
- Gombok keresése template alapján (nem fix koordináták)
- Multi-scale matching (több méret próbálása)

**Fontos:** Template matching NEM "tanulja meg" a gombokat! Csak összehasonlítja a mentett képet a képernyővel.

**Használat:**

#### 1. **Template Capture (gomb mentése)**
```bash
python setup_wizard.py
# Válaszd: 9. Advanced Tools
# Válaszd: 1. Capture Button Template
```

Vagy batch capture:
```bash
# Wizard → 9. Advanced Tools → 4. Batch Template Capture
# Mentse mind a 4 training building gombot egyszerre
```

#### 2. **Template Matching Test**
```bash
# Wizard → 9. Advanced Tools → 2. Test Template Matching
# Válassz egy template-et → teszt
```

#### 3. **Kódban használat**
```python
from library import ImageManager

# Template keresése
coords = ImageManager.find_image('images/barracks_button.png', threshold=0.7)

# Multi-scale matching (robusztusabb, de lassabb)
coords = ImageManager.find_image('images/barracks_button.png', threshold=0.7, multi_scale=True)

if coords:
    safe_click(coords)
```

**Előnyök:**
- ✅ Ablak méret változás nem probléma (multi-scale)
- ✅ Robusztusabb mint fix koordináták
- ✅ Kis pozíció eltolódást kezel

**Hátrányok:**
- ⚠️  Lassabb mint koordináta-alapú (0.5-2 sec keresés)
- ⚠️  **Új template kell ha UI változik** (pl. skin, update) - mert NEM tanul, csak összehasonlít!
- ⚠️  Template-ek tárolása (minden gombhoz 1 kép)

---

### **Advanced Tools Menu**

**Elérés:** `setup_wizard.py` → 9. Advanced Tools

#### **1. Capture Button Template**
- Koordinátából készít template-et
- Kattintással vagy manuális input
- Egyedi méret megadása (default: 80x80)

#### **2. Test Template Matching**
- Template keresése a képernyőn
- Threshold beállítás (0.0-1.0)
- Multi-scale opció

#### **3. Test EasyOCR vs Tesseract**
- OCR engine összehasonlítás
- Training/Resource régió választás
- Élő teszt + debug save

#### **4. Batch Template Capture**
- Több gomb egyszerre
- Training: 4 building gomb
- Gathering: map, search gomb
- Alliance: alliance, help gomb

---

## 📝 Fejlesztési Roadmap

- [x] ~~Machine learning OCR (Tesseract helyett)~~ - **KÉSZ (EasyOCR)**
- [x] ~~Template matching alapú gomb keresés~~ - **KÉSZ**
- [ ] Relatív koordináták támogatás (%-os értékek)
- [ ] Auto-calibration (template matching alapján)
- [ ] Hybrid mode (koordináta + template fallback)
- [ ] Web UI config editor
- [ ] Real-time monitoring dashboard

---

## 🆕 Változások Log

### v2.1 ML-Enhanced (2025-12-10)
- ✅ EasyOCR támogatás (ML-alapú OCR)
- ✅ Enhanced template matching (multi-scale)
- ✅ Button template capture tool
- ✅ Advanced Tools menu wizard-ban
- ✅ OCR comparison tool (EasyOCR vs Tesseract)
- ✅ Batch template capture

### v2.0 Complete (előző)
- ✅ Module-specific testing (training/gathering/explorer)
- ✅ Config validator + visualizer
- ✅ OCR preprocessing (OTSU, Adaptive, CLAHE)
- ✅ Progressive retry logic
- ✅ ESC + 2x SPACE clean state

---

**Kérdés van? Nézd meg a log fájlokat:** `logs/farm_YYYYMMDD_HHMMSS.log`
