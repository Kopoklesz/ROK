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

## 🛠️ Config Validator Tool

### Használat

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

## 📝 Fejlesztési Roadmap (Ötletek)

- [ ] Relatív koordináták támogatás (%-os értékek)
- [ ] Auto-calibration (template matching alapján)
- [ ] Machine learning OCR (Tesseract helyett)
- [ ] Web UI config editor
- [ ] Real-time monitoring dashboard

---

**Kérdés van? Nézd meg a log fájlokat:** `logs/farm_YYYYMMDD_HHMMSS.log`
