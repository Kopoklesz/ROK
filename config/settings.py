"""
Projekt konfigurációs beállítások
"""
import os
from pathlib import Path

# ===== PROJEKT ÚTVONALAK =====
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = DATA_DIR / "models"
LOGS_DIR = DATA_DIR / "logs"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"

# Könyvtárak létrehozása
for directory in [TEMPLATES_DIR, DATA_DIR, MODELS_DIR, LOGS_DIR, SCREENSHOTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ===== JÁTÉK BEÁLLÍTÁSOK =====
GAME_WINDOW_TITLE = "BlueStacks App Player"  # Módosítsd a saját emulátorodra
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ===== KÉPFELISMERÉS =====
TEMPLATE_MATCHING_THRESHOLD = 0.7  # 0-1 közötti érték, magasabb = szigorúbb
SCREENSHOT_DELAY = 0.3  # Várakozás képernyőkép után (másodperc)
ACTION_DELAY_MIN = 0.5  # Minimum várakozás akciók között
ACTION_DELAY_MAX = 1.5  # Maximum várakozás akciók között

# ===== OCR BEÁLLÍTÁSOK =====
OCR_CONFIG = '--psm 7 --oem 3'  # Tesseract config (single line text)
OCR_CONFIDENCE_THRESHOLD = 60  # Minimum confidence (0-100)

# ===== NEURAL NETWORK =====
STATE_SHAPE = (84, 84, 3)  # Screenshot átméretezés (height, width, channels)
ACTION_SPACE_SIZE = 20  # Lehetséges akciók száma (később bővül)
LEARNING_RATE = 0.0001
GAMMA = 0.99  # Discount factor
BATCH_SIZE = 32
MEMORY_SIZE = 10000
TARGET_UPDATE_FREQUENCY = 10  # Epizódok száma target network frissítésig

# ===== EXPLORATION =====
EPSILON_START = 1.0
EPSILON_END = 0.1
EPSILON_DECAY = 0.995

# ===== TRAINING =====
NUM_EPISODES = 1000
MAX_STEPS_PER_EPISODE = 500
SAVE_FREQUENCY = 50  # Modell mentés gyakorisága (epizódok)

# ===== REWARD SÚLYOK =====
# Ezeket később rewards.yaml-ből töltjük be
REWARD_WEIGHTS = {
    # Pozitív reward-ok
    'barracks_opened': 0.2,
    'train_menu_opened': 0.2,
    'tier_selected': 0.1,
    'quantity_set': 0.1,
    'train_button_clicked': 0.3,
    'training_started': 1.0,
    'power_increased': 0.5,
    
    # Negatív reward-ok
    'wasted_click': -0.1,
    'idle_too_long': -0.2,
    'resource_depleted': -0.5,
    'failed_action': -0.3,
    'queue_busy_attempt': -1.0
}

# ===== DEBUG & LOGGING =====
DEBUG_MODE = True
SAVE_DEBUG_SCREENSHOTS = True
VERBOSE_LOGGING = True
TENSORBOARD_LOG_DIR = LOGS_DIR / "tensorboard"

# ===== KOORDINÁTÁK (példák - módosítsd a sajátodra!) =====
# Ezeket a collect_templates.py segítségével gyűjtöd be
SCREEN_REGIONS = {
    'city_center': (500, 300, 800, 600),  # (x, y, width, height)
    'resources': (50, 50, 300, 100),
    'power_display': (100, 100, 200, 50),
    'queue_status': (1400, 50, 100, 100),
    'building_list': (50, 200, 200, 600)
}

# ===== AKCIÓK DEFINÍCIÓJA =====
ACTIONS = {
    0: {'name': 'wait', 'duration': 1.0},
    1: {'name': 'navigate_barracks', 'target': 'barracks'},
    2: {'name': 'navigate_archery', 'target': 'archery'},
    3: {'name': 'navigate_stable', 'target': 'stable'},
    4: {'name': 'navigate_siege', 'target': 'siege'},
    5: {'name': 'click_train_button', 'template': 'ui/train_button.png'},
    6: {'name': 'click_tier_t1', 'template': 'tiers/tier_t1.png'},
    7: {'name': 'click_tier_t2', 'template': 'tiers/tier_t2.png'},
    8: {'name': 'click_tier_t3', 'template': 'tiers/tier_t3.png'},
    9: {'name': 'click_tier_t4', 'template': 'tiers/tier_t4.png'},
    10: {'name': 'click_tier_t5', 'template': 'tiers/tier_t5.png'},
    11: {'name': 'set_quantity_min', 'value': 1},
    12: {'name': 'set_quantity_low', 'value': 100},
    13: {'name': 'set_quantity_medium', 'value': 500},
    14: {'name': 'set_quantity_high', 'value': 1000},
    15: {'name': 'set_quantity_max', 'value': -1},  # -1 = max
    16: {'name': 'click_confirm', 'template': 'ui/confirm_button.png'},
    17: {'name': 'click_close', 'template': 'ui/close_button.png'},
    18: {'name': 'go_to_city', 'coords': (640, 360)},  # Példa fix koordináta
    19: {'name': 'emergency_escape', 'key': 'esc'}
}

print(f"✅ Config betöltve: {len(ACTIONS)} akció definiálva")