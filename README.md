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
4. Módosítsd az útvonalat (25. sor):

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### C) Játék ablak nevének beállítása

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

**Ha minden kész, jó farmolást!** 🌾🚜



**Jövő**

-Szövetségi rally csatlakozás
-Szövetségi rally indítás
-Fő épület fejlesztés

**Javítás**

-Szövetségi segítségnyújtás
-Fagyás elleni védelem
-Város nézet elleni védelem
-Szövetségi 
