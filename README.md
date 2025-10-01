# 🎮 ROK RL Agent - Rise of Kingdoms Reinforcement Learning Bot

Mesterséges intelligencia agent, amely **megerősítéses tanulással** (Deep Q-Learning) tanul meg Rise of Kingdoms játékot játszani.

---

## 📋 Tartalomjegyzék

- [Jellemzők](#-jellemzők)
- [Telepítés](#-telepítés)
- [Használat](#-használat)
- [Template gyűjtés](#-template-gyűjtés)
- [Training](#-training)
- [Architektúra](#-architektúra)
- [Konfigur](#-konfiguration)

---

## ✨ Jellemzők

- **Deep Q-Network (DQN)** neurális háló
- **Pixel-based learning** - képernyőből tanul
- **Reward shaping** - részfeladatok jutalmazása
- **Template matching** - UI elemek felismerése
- **OCR támogatás** - szöveg/szám kiolvasás
- **Tensorboard integráció** - training vizualizáció
- **Modular design** - könnyen bővíthető

---

## 🔧 Telepítés

### 1. Előfeltételek

- **Python 3.10+**
- **Tesseract OCR** ([letöltés](https://github.com/UB-Mannheim/tesseract/wiki))
- **CUDA** (opcionális, GPU gyorsításhoz)
- **BlueStacks** vagy más Android emulátor

### 2. Repository klónozása

```bash
git clone https://github.com/yourusername/rok-rl-agent.git
cd rok-rl-agent
```

### 3. Virtual environment létrehozása

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 4. Csomagok telepítése

```bash
pip install -r requirements.txt
```

### 5. Tesseract beállítása

Szerkeszd `config/settings.py`:
```python
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

---

## 🚀 Használat

### Gyors start (3 lépésben)

#### 1. Template képek gyűjtése

```bash
python collect_templates.py
```

**Ezt kell csinálnod:**
1. Indítsd el a játékot (BlueStacks)
2. Futtasd a scriptet
3. Jelöld ki egérrel a kért UI elemeket
4. Nyomj ENTER-t minden mentéshez

**Gyűjtendő képek:**

| Kategória | Template | Leírás |
|-----------|----------|--------|
| **Buildings** | `barracks_icon.png` | Barakk ikon |
| | `archery_icon.png` | Íjász tábor ikon |
| | `stable_icon.png` | Istálló ikon |
| | `siege_icon.png` | Ostromműhely ikon |
| **UI** | `train_button.png` | "Train" gomb |
| | `zzzz_icon.png` | Foglalt queue ikon |
| | `confirm_button.png` | Megerősítés gomb |
| | `train_menu_header.png` | Képzés menü fejléc |
| **Tiers** | `tier_t1.png` ... `tier_t5.png` | T1-T5 szint ikonok |

#### 2. Environment tesztelés

```bash
python test_environment.py
```

Válaszd a **4. Interaktív teszt** módot és próbálj ki néhány akciót.

#### 3. Training indítása

```bash
python train.py --episodes 100
```

---

## 📸 Template Gyűjtés - Részletes útmutató

### Automatikus módszer

```bash
python collect_templates.py
```

Válaszd az **1. Template képek gyűjtése** opciót.

### Mi történik lépésről-lépésre:

1. **Ablak fókusz**: Script automatikusan rákeres a játék ablakra
2. **Területkijelölés**: 
   - Bal egérgombbal jelöld ki a területet
   - Húzd végig az elemet (pl. Train gomb)
   - Nyomj **ENTER**-t a mentéshez
3. **Következő elem**: Automatikusan lép tovább
4. **Befejezés**: Összes template összegyűjtve

### Koordináták gyűjtése (opcionális)

```bash
python collect_templates.py
```

Válaszd a **2. Koordináták gyűjtése** opciót, majd:
- Kattints a fontos pontokra (város középpont, épületek)
- Írj be nevet minden koordinátához
- Nyomj **ESC**-et a befejezéshez

Mentés helye: `templates/coordinates.json`

---

## 🏋️ Training

### Alapvető training

```bash
python train.py
```

### Paraméterek

```bash
python train.py --episodes 500 --dueling
```

| Paraméter | Leírás | Default |
|-----------|--------|---------|
| `--episodes` | Epizódok száma | 1000 |
| `--dueling` | Dueling DQN használata | False |
| `--resume` | Model folytatása | None |

### Training folytatása

```bash
python train.py --resume data/models/dqn_agent_ep100.pth
```

### Training monitorozás

**Tensorboard** (TODO - később implementálható):
```bash
tensorboard --logdir data/logs/tensorboard
```

**Log fájlok**:
- `data/logs/training_YYYYMMDD_HHMMSS.json`

**Grafikonok**:
- `data/models/training_plot_epXXX.png`

---

## 🏗️ Architektúra

### Fő komponensek

```
rok-rl-agent/
│
├── core/                    # Alapvető funkciók
│   ├── window_manager.py   # Ablakkezelés
│   ├── image_manager.py    # Képfelismerés, OCR
│   └── action_executor.py  # Kattintások
│
├── environment/             # RL környezet
│   ├── rok_env.py          # Fő environment
│   └── reward_manager.py   # Jutalom számítás
│
├── agent/                   # Neural network
│   ├── network.py          # DQN architektúra
│   ├── replay_buffer.py    # Experience replay
│   └── dqn_agent.py        # RL agent
│
└── utils/                   # Segédfunkciók
    ├── logger.py
    └── visualizer.py
```

### Neural Network

**DQN (Deep Q-Network)**:
- Input: 84x84x3 screenshot (RGB)
- 3x Convolutional layer
- 2x Fully connected layer
- Output: Q-values (20 akció)

**Dueling DQN** (advanced):
- Külön Value és Advantage stream
- Jobb konvergencia

### Reward rendszer

| Esemény | Reward | Detektálás |
|---------|--------|------------|
| ✅ Képzés elindult | +1.0 | Zzzz ikon megjelent |
| ✅ Barakk megnyitva | +0.2 | Template match |
| ✅ Train menü nyitva | +0.2 | Tier ikonok |
| ✅ Train gomb kattintva | +0.3 | Gomb eltűnt |
| ❌ Foglalt queue-ba próbált | -1.0 | Zzzz látható |
| ❌ Felesleges kattintás | -0.1 | Nincs változás |
| ❌ Erőforrás kifogyott | -0.5 | OCR |

---

## ⚙️ Konfiguráció

### settings.py módosítása

```python
# config/settings.py

# Játék ablak neve
GAME_WINDOW_TITLE = "BlueStacks App Player"  # Változtasd meg!

# Template matching pontosság
TEMPLATE_MATCHING_THRESHOLD = 0.7  # 0.6-0.8 ajánlott

# Neural network
LEARNING_RATE = 0.0001
BATCH_SIZE = 32
MEMORY_SIZE = 10000

# Training
NUM_EPISODES = 1000
MAX_STEPS_PER_EPISODE = 500

# Exploration
EPSILON_START = 1.0    # 100% random kezdetben
EPSILON_END = 0.1      # 10% random végül
EPSILON_DECAY = 0.995
```

### Reward súlyok módosítása

```python
REWARD_WEIGHTS = {
    'training_started': 1.0,      # FŐ JUTALOM
    'barracks_opened': 0.2,       # Kisebb lépések
    'wasted_click': -0.1,         # Büntetések
}
```

---

## 🐛 Hibakeresés

### Template nem található

**Probléma**: `⚠️ Template nem található: ui/train_button.png`

**Megoldás**:
1. Ellenőrizd hogy létezik-e: `templates/ui/train_button.png`
2. Gyűjtsd újra: `python collect_templates.py`
3. Csökkentsd a threshold-ot: `TEMPLATE_MATCHING_THRESHOLD = 0.6`

### Ablak nem található

**Probléma**: `❌ Nem található a játék ablak!`

**Megoldás**:
1. Indítsd el a játékot
2. Módosítsd `GAME_WINDOW_TITLE` a `config/settings.py`-ben
3. Futtasd `test_environment.py` → válassz ablakot

### OCR nem működik

**Probléma**: `❌ OCR hiba`

**Megoldás**:
1. Telepítsd Tesseract-ot
2. Állítsd be `TESSERACT_PATH` értékét
3. Teszteld: `pytesseract.get_tesseract_version()`

### GPU nem használódik

**Probléma**: CPU-n fut (lassú)

**Megoldás**:
```bash
# CUDA telepítése után
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

---

## 📊 Eredmények értelmezése

### Training grafikonok

1. **Episode Rewards**: Javul-e az agent?
   - Növekvő trend = tanul ✅
   - Random = nem tanul ❌

2. **Loss**: Neural network tanulás
   - Csökkenő = jó
   - Stabil ~0.1-0.5 = konvergált

3. **Epsilon**: Exploration decay
   - 1.0 → 0.1 fokozatos csökkenés

4. **Cumulative Reward**: Összteljesítmény
   - Pozitív = jó irány
   - Negatív = rossz reward design

### Mikor sikeres a training?

✅ **Sikeres tanulás jelei:**
- Episode reward növekszik
- Loss stabilizálódik
- Agent képes képzést elindítani
- Nem próbál foglalt queue-ba képezni

❌ **Problémák:**
- Reward nem változik → Rossz reward design
- Loss nő → Learning rate túl magas
- Random viselkedés → Túl kevés tapasztalat

---

## 🔮 Továbbfejlesztési ötletek

- [ ] Multi-building support (több épület párhuzamosan)
- [ ] Resource management (erőforrás gyűjtés)
- [ ] Building upgrades (fejlesztések)
- [ ] Research (kutatások)
- [ ] Commander management
- [ ] PvP stratégiák
- [ ] Prioritized Experience Replay
- [ ] Double DQN / Rainbow DQN
- [ ] Curriculum learning

---

## 📞 Támogatás

**Problémák esetén:**
1. Ellenőrizd `data/logs/` fájlokat
2. Futtasd `test_environment.py` diagnosztikát
3. Nyiss issue-t GitHub-on

---

## 📄 Licenc

MIT License - szabadon használható és módosítható

---

## 🙏 Köszönetnyilvánítás

- OpenAI Gym/Gymnasium inspiráció
- DeepMind DQN paper
- Rise of Kingdoms játék

---

**Készítette**: ROK RL Team  
**Verzió**: 1.0.0  
**Utolsó frissítés**: 2024

---

**Jó játékot és sikeres tréninget!** 🚀🎮