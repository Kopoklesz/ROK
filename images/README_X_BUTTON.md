# X Gomb Template Beállítása

## Mi ez?

Az **automatikus popup bezárás** mechanizmus, ami X gombot keres és rákattint, ha az OCR szemét szöveget olvas.

## Hogyan működik?

1. **Training/Explorer OCR hiba** esetén (szemét szöveg: 'TS Un &', 'Wh ne', stb.)
2. **X gomb keresés** aktiválódik (template matching)
3. Ha **megtalálja az X gombot** → **Rákattint** → Popup bezárul
4. **OCR újrapróbálás** (már tiszta képernyővel)

## Setup lépések:

### 1. Készíts screenshot-ot egy X gombról

- Nyiss meg egy **popup-ot** a játékban (pl. level up, notification, stb.)
- Készíts **screenshot-ot** (Windows: `Win + Shift + S`)
- Vágd ki **CSAK az X gombot** (20x20 - 40x40 pixel körül)

### 2. Mentsd el a template-et

Mentsd el az alábbi nevek **egyikével**:

```
images/close_x.png       ← Preferált
images/x_button.png
images/popup_close.png
```

### 3. Template minősége

**JÓ példa:**
```
┌─────┐
│  ✕  │  ← Tiszta X, éles szélek, jó kontraszt
└─────┘
```

**ROSSZ példa:**
```
┌─────────────┐
│ OK    ✕     │  ← Túl nagy, sok extra terület
└─────────────┘
```

### 4. Tesztelés

Futtasd a bot-ot és nézd a logot:
```
[Popup Close] X gomb keresése: close_x.png
[Popup Close] Próbálkozás 1/2...
[Popup Close] ✓ X gomb megtalálva → (1234, 567)
[Popup Close] ✓ Popup bezárva
```

## Threshold beállítás

Ha **túl sokszor talál** hamis pozitívokat:
- Növeld a threshold-ot: `0.65 → 0.75` (library.py, training_manager.py, explorer.py)

Ha **nem találja meg** az X gombot:
- Csökkentsd a threshold-ot: `0.65 → 0.55`

## Troubleshooting

### "X gomb nem található"
- ✅ Ellenőrizd hogy létezik: `images/close_x.png`
- ✅ Túl kicsi a template? (min 15x15 pixel)
- ✅ Túl nagy a template? (max 50x50 pixel)
- ✅ Rossz threshold? (próbálj 0.6-ot)

### "Rossz helyre kattint"
- ✅ Vágd ki PONTOSAN csak az X gombot
- ✅ Ne legyen extra háttér körülötte
- ✅ Növeld a threshold-ot (0.75-0.8)

## Technikai részletek

**Mikor aktiválódik?**
- Training OCR: Minden 3. sikertelen próbálkozás után (3., 6., 9.)
- Explorer OCR: Azonnal, ha nincs % jel

**Hol keres?**
- Teljes képernyőn (nincs korlátozva régióra)

**Max próbálkozások:**
- 2 próba X gomb kereséséhez
- 0.65 threshold (65% egyezés kell)
