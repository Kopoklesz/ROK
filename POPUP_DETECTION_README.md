# Intelligens Popup Detektálás és Bezárás

## Áttekintés

A rendszer automatikusan felismeri és bezárja a popup ablakokat, amikor az OCR rossz (szemét) szövegeket olvas ki.

## Működés

### 1. Szemét OCR Detektálás

Az `is_garbage_ocr_text()` függvény felismeri a rossz OCR eredményeket:

**Példák szemét szövegekre:**
- `'Wi} 2'` (helyett: `'95%'`)
- `'King's'` (helyett: `'Ancient'`)
- `'iim'` (helyett: `'Ruins'`)
- `'TS Un &'` (random karakterek)
- `'Wh ne'` (szétszakadt szavak)

**Detektálási szabályok:**
- Ismert szemét minták (regex alapú)
- Túl sok speciális karakter (30%+)
- Túl rövid lowercase szavak

### 2. Explorer - Scout Panel OCR

**Aktiválási feltétel:**
- 2+ régióból szemét OCR szöveg érkezik (3-ból)
- Hiányzó % jelek (nincs felfedezés folyamatban)

**Működés:**
1. Detektálja a szemét szövegeket
2. X gomb keresés és kattintás (3 próba, 0.7 threshold)
3. Scout panel újranyitása
4. OCR újrapróbálás tiszta képernyővel

**Kód helye:** [explorer.py:133-190](explorer.py#L133-L190)

### 3. Training Manager - Panel OCR

**Aktiválási feltétel:**
- 2+ egymást követő sikertelen OCR próba
- OCR szöveg szemét (garbage)
- Idő parse sikertelen

**Működés:**
1. Detektálja a szemét OCR szöveget
2. X gomb keresés és kattintás (2 próba, 0.75 threshold)
3. Queue panel bezárás + újranyitás
4. OCR újrapróbálás tiszta képernyővel

**Kód helye:** [managers/training_manager.py:383-420](managers/training_manager.py#L383-L420)

## X Gomb Template-ek

A rendszer az alábbi template-eket keresi (prioritás sorrendben):

1. `images/close_x.png` (elsődleges)
2. `images/x_button.png` (másodlagos)
3. `images/popup_close.png` (harmadlagos)

**Template követelmények:**
- Méret: 15x15 - 50x50 pixel
- Csak az X gombot tartalmazza (nincs extra háttér)
- Éles szélek, jó kontraszt

## Popup Keresési Régió

Az X gomb keresés gyorsítható és pontosítható egy keresési régió megadásával:

**Konfiguráció:** `config/popup_regions.json`
```json
{
  "popup_search_region": {
    "x": 0,
    "y": 0,
    "width": 1920,
    "height": 1080,
    "description": "X button search region for popup detection"
  }
}
```

**Előnyök:**
- Gyorsabb X gomb keresés (csak a megadott területen keres)
- Kevesebb hamis pozitív (épület ikonok, egyéb X-ek kizárása)
- Optimalizált teljesítmény (kisebb keresési terület)

**Beállítás:**
- Setup Wizard → Advanced Tools → Option 6: Setup Popup Search Region
- Jelöld ki a területet ahol popup ablakok megjelennek (általában képernyő közepe/felső része)

## Threshold Beállítások

### Explorer
- **Max próbák:** 3
- **Threshold:** 0.7 (70% egyezés)

### Training Manager
- **Max próbák:** 2
- **Threshold:** 0.75 (75% egyezés - szigorúbb, kevesebb hamis pozitív)

## Logok

**Popup detektálás:**
```
⚠️ Szemét OCR szövegek (3/3) → Popup valószínű!
🔍 X gomb keresés aktiválva (popup bezárás)...
[Popup Close] X gomb keresése: close_x.png
[Popup Close] Próbálkozás 1/3...
[Popup Close] ✓ X gomb megtalálva → (1234, 567)
[Popup Close] ✓ Popup bezárva
✅ Popup bezárva! Scout panel újranyitása...
```

**Normális működés (nincs popup):**
```
ℹ️ Normális OCR szövegek → Scout indítás szükséges
```

## Előnyök

### Korábbi megoldás problémái:
- ❌ Mindig futott (túl agresszív)
- ❌ Hamis pozitívok (épület ikonok, stb.)
- ❌ Random navigáció

### Új intelligens megoldás:
- ✅ Csak szemét OCR esetén aktiválódik
- ✅ 2+ sikertelen próba után (türelmes)
- ✅ Konszenzus alapú detektálás (több régió)
- ✅ Magasabb threshold (kevesebb hamis pozitív)
- ✅ Panel újranyitás az OCR előtt

## Debugging

### Ha nem találja meg az X gombot:
1. Ellenőrizd hogy létezik: `images/close_x.png`
2. Csökkentsd a threshold-ot: `0.7 → 0.6`
3. Ellenőrizd a template méretét (15-50px)

### Ha hamis pozitívokat talál:
1. Növeld a threshold-ot: `0.7 → 0.8`
2. Vágd ki pontosabban az X gombot (kevesebb háttér)
3. Ellenőrizd a szemét szöveg mintákat

## Kapcsolódó Fájlok

- [library.py:427-469](library.py#L427-L469) - `is_garbage_ocr_text()` függvény
- [library.py:472-535](library.py#L472-L535) - `find_and_close_popups()` függvény
- [explorer.py:133-190](explorer.py#L133-L190) - Explorer implementáció
- [managers/training_manager.py:383-420](managers/training_manager.py#L383-L420) - Training Manager implementáció
- [images/README_X_BUTTON.md](images/README_X_BUTTON.md) - X gomb template dokumentáció
