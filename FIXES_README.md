# 🔧 ROK Auto Farm - Javítások Dokumentációja

**Dátum:** 2025-12-07
**Verzió:** 1.1.0-Improving

---

## ✅ JAVÍTOTT HIBÁK

### 1️⃣ **gathering_manager.py - Rossz fájlnév**

**Hiba:** A manager `resource_regions.json`-t kereste, de a fájl `farm_regions.json` néven létezik.

**Fájl:** `managers/gathering_manager.py:134`

**FIX:**
```python
# ELŐTTE
resource_regions_file = self.config_dir / 'resource_regions.json'

# UTÁNA
resource_regions_file = self.config_dir / 'farm_regions.json'
```

**Hatás:** Most már helyesen beolvassa az erőforrásokat és nem mindig wheat-et választ!

---

### 2️⃣ **training_manager.py - enabled/disabled logika invertálva**

**Hiba:** A kód `disabled` mezőt keresett a config-ban, de `enabled` volt benne. Emiatt minden building mindig disabled volt!

**Fájl:** `managers/training_manager.py:101`

**FIX:**
```python
# ELŐTTE
enabled = building_config.get('disabled', False)

# UTÁNA
enabled = building_config.get('enabled', True)
```

**Hatás:** Most már működik a training manager!

---

### 3️⃣ **alliance_manager.py - hand_locations használatlan**

**Hiba:** A kód template matching-et használt a teljes képernyőn, de nem használta a `hand_locations` fix koordinátákat, amik pontosabbak és gyorsabbak.

**Fájl:** `managers/alliance_manager.py:104-196`

**FIX:** Új stratégia implementálva:
1. **Először:** Fix koordináták próbálása (`hand_locations`) - gyorsabb, megbízhatóbb
2. **Fallback:** Template matching, ha nincs fix koordináta

**Hatás:** Alliance help most sokkal megbízhatóbban működik!

---

### 4️⃣ **setup_wizard.py - Hiányzó függvények**

**Hiba:** A fájl csonka volt (166. sor után `# ... (további függvények változatlanul) ...` komment, de nincs kód!)

**Fájl:** `setup_wizard.py`

**HIÁNYZOTT:**
- `setup_resource_regions()` - Resource OCR régiók
- `setup_time_regions()` - Time OCR régiók
- `setup_farm_coordinates()` - Farm koordináták
- `setup_gather_template()` - gather.png template
- `training_menu()` - Training setup menü
- `setup_training_time_regions()` - Training time régiók
- `setup_training_coordinates()` - Training koordináták
- `alliance_menu()` - Alliance setup menü
- `setup_hand_locations()` - Hand koordináták
- `setup_hand_template()` - hand.png template
- `anti_afk_menu()` - Anti-AFK setup menü
- `setup_resource_templates()` - Resource templates
- `settings_menu()` - Settings szerkesztő
- `test_menu()` - Test & Verify

**FIX:** Teljes setup_wizard.py újraírva minden hiányzó függvénnyel!

**Backup:** `setup_wizard_old.py` és `setup_wizard.py.backup`

**Hatás:** Most már működik a teljes setup wizard!

---

## ⚠️ ISMERT PROBLÉMÁK (MANUÁLIS JAVÍTÁS SZÜKSÉGES)

### 5️⃣ **time_regions.json - gather_time régió túl széles**

**Probléma:** `config/time_regions.json:8-12`

```json
"gather_time": {
  "x": 74,
  "y": 585,
  "width": 1688,  // ❌ MAJDNEM A TELJES KÉPERNYŐ SZÉLESSÉGE!
  "height": 72
}
```

**Hatás:**
- OCR több szöveget is beolvas egyszerre
- Parse hiba
- 60 retry után fail → 5 perc késleltetés

**MEGOLDÁS:**
1. Futtasd: `python setup_wizard.py`
2. Válaszd: `1. Gathering Setup`
3. Válaszd: `2. Time Regions`
4. **gather_time** kijelölésekor:
   - ⚠️ **CSAK az időt jelöld ki!** (pl. "5m 30s" vagy "1h 20m")
   - ❌ **NE** a teljes sort!
   - ❌ **NE** a környező szöveget!
5. A régió szélessége ideálisan **50-150 pixel** legyen, NE 1688!

**Jelenlegi érték:** width: 1688 px
**Ajánlott érték:** width: 80-120 px (csak az idő szöveg szélessége)

---

## 📝 TESZTELÉSI CHECKLIST

Setup wizard újrafuttatása után ellenőrizd:

- [ ] **Resource regions** - 4 erőforrás régió beállítva (wheat, wood, stone, gold)
- [ ] **Time regions** - march_time ÉS gather_time **PONTOSAN** beállítva
  - [ ] gather_time width < 200 px ⚠️ KRITIKUS!
- [ ] **Farm coordinates** - Mind a 4 farm típushoz 6 koordináta
- [ ] **gather.png** - Template létezik
- [ ] **march.png** - Template létezik
- [ ] **March detection region** - Régió beállítva
- [ ] **Training time regions** - 4 épület time régió
- [ ] **Training coordinates** - 4 épület × 5 koordináta
- [ ] **Hand locations** - 2 koordináta beállítva
- [ ] **hand.png** - Template létezik (opcionális)
- [ ] **Resource templates** - resource1-4.png létezik (opcionális)

---

## 🚀 HASZNÁLAT

### Setup Wizard futtatása:
```bash
python setup_wizard.py
```

### Main program futtatása:
```bash
python farm_manager.py
```

### Leállítás:
```
CTRL+C
```

---

## 📊 ÖSSZEFOGLALÁS

| Hiba | Típus | Státusz | Automatikus javítás |
|------|-------|---------|---------------------|
| gathering_manager.py fájlnév | Kritikus | ✅ JAVÍTVA | Igen |
| training_manager.py enabled | Kritikus | ✅ JAVÍTVA | Igen |
| alliance_manager.py hand_locations | Közepes | ✅ JAVÍTVA | Igen |
| setup_wizard.py hiányzó függvények | Kritikus | ✅ JAVÍTVA | Igen |
| gather_time régió túl széles | Magas | ⚠️ MANUÁLIS | **NEM** - setup wizard |

---

## 🔧 EREDETI FÁJLOK BACKUPJA

- `setup_wizard.py.backup` - Eredeti csonka verzió
- `setup_wizard_old.py` - Eredeti csonka verzió (átnevezve)

Visszaállítás (ha szükséges):
```bash
mv setup_wizard_old.py setup_wizard.py
```

---

## 📞 TOVÁBBI SEGÍTSÉG

Ha problémád van:
1. Ellenőrizd a `logs/` könyvtárban a log fájlokat
2. Futtasd újra a setup wizard-ot
3. Nézd meg a `config/` könyvtárban a mentett beállításokat

---

**Jó farmolást!** 🌾🚜
