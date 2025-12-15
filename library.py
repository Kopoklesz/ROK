"""
ROK Auto Farm - Library
Alapvető függvények a meglévő library alapján
FIXED: WindowManager.find_window() exception handling
ENHANCED: EasyOCR support + Template matching improvements
"""
import time
import random
import pyautogui
import cv2
import numpy as np
import pytesseract
from PIL import ImageGrab, Image
import win32gui
import win32con
from pynput.keyboard import Controller, Key
from pathlib import Path

# DPI awareness
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# Tesseract path - MÓDOSÍTSD A SAJÁTODRA!
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# EasyOCR support (optional)
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    _easyocr_reader = None
    print("✅ EasyOCR elérhető - ML-alapú OCR használata")
except ImportError:
    EASYOCR_AVAILABLE = False
    print("⚠️  EasyOCR nincs telepítve - Tesseract fallback használata")
    print("   Telepítés: pip install easyocr")

# Globális változók
game_window_handle = None
game_window_title = "BlueStacks"  # Módosítsd a játék ablak nevére
keyboard = Controller()

# pyautogui beállítások
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


class WindowManager:
    """Ablakkezelés"""
    
    @staticmethod
    def find_window(partial_title=None):
        """
        Játék ablak keresése
        
        FIXED: Exception handling win32gui.EnumWindows() callback-nél
        """
        global game_window_handle, game_window_title
        
        if partial_title is None:
            partial_title = game_window_title
        
        # Flag lista (mutable, így a callback módosíthatja)
        found = [False]
        
        def callback(hwnd, extra):
            # Ha már találtunk ablakot, skip further checks
            if found[0]:
                return True
            
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if partial_title.lower() in title.lower():
                        global game_window_handle
                        game_window_handle = hwnd
                        found[0] = True
            except:
                pass
            
            return True  # FONTOS: Mindig True-t adunk vissza, így nem lesz exception
        
        try:
            win32gui.EnumWindows(callback, None)
            return found[0]
        except Exception as e:
            print(f"Ablak keresési hiba: {e}")
            return False
    
    @staticmethod
    def focus_window():
        """Fókusz a játék ablakra"""
        if game_window_handle:
            try:
                win32gui.ShowWindow(game_window_handle, win32con.SW_RESTORE)
                time.sleep(0.1)
                win32gui.SetForegroundWindow(game_window_handle)
                time.sleep(0.1)
                return True
            except:
                return False
        return False
    
    @staticmethod
    def get_window_rect():
        """Ablak pozíció és méret"""
        if game_window_handle:
            try:
                rect = win32gui.GetWindowRect(game_window_handle)
                x, y, right, bottom = rect
                return (x, y, right - x, bottom - y)
            except:
                return None
        return None


class ImageManager:
    """Képfelismerés és OCR"""
    
    @staticmethod
    def screenshot(region=None):
        """Képernyőkép készítése"""
        try:
            if region is None:
                rect = WindowManager.get_window_rect()
                if rect:
                    region = rect
            
            img = pyautogui.screenshot(region=region)
            img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            return img_np
        except Exception as e:
            print(f"Screenshot hiba: {e}")
            return None
    
    @staticmethod
    def find_image(template_path, threshold=0.7, multi_scale=False, search_region=None):
        """
        Template matching - ENHANCED verzió

        Args:
            template_path: Template kép elérési útja
            threshold: Egyezési küszöb (0-1)
            multi_scale: Ha True, több skálán is próbál (lassabb, de robusztusabb)
            search_region: dict - Keresési régió {'x', 'y', 'width', 'height'}
                          Ha None, akkor teljes képernyő

        Returns:
            tuple: (x, y) koordináták vagy None
        """
        try:
            # Template betöltése
            template = cv2.imread(template_path)
            if template is None:
                print(f"⚠️  Template nem található: {template_path}")
                return None

            # Screenshot
            screen = ImageManager.screenshot()
            if screen is None:
                return None

            # Régió alapú keresés
            region_offset_x = 0
            region_offset_y = 0
            if search_region:
                x = search_region.get('x', 0)
                y = search_region.get('y', 0)
                w = search_region.get('width', screen.shape[1])
                h = search_region.get('height', screen.shape[0])

                # Screenshot régió kivágása
                screen = screen[y:y+h, x:x+w]
                region_offset_x = x
                region_offset_y = y

            best_match = None
            best_val = threshold

            # Multi-scale matching (opcionális)
            scales = [1.0]
            if multi_scale:
                scales = [0.8, 0.9, 1.0, 1.1, 1.2]

            for scale in scales:
                # Template átméretezése
                if scale != 1.0:
                    width = int(template.shape[1] * scale)
                    height = int(template.shape[0] * scale)
                    resized = cv2.resize(template, (width, height))
                else:
                    resized = template

                # Matching
                result = cv2.matchTemplate(screen, resized, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                # Jobb match?
                if max_val > best_val:
                    best_val = max_val
                    h, w = resized.shape[:2]
                    center_x = max_loc[0] + w // 2 + region_offset_x
                    center_y = max_loc[1] + h // 2 + region_offset_y

                    # Relatív → Abszolút koordináták
                    rect = WindowManager.get_window_rect()
                    if rect:
                        center_x += rect[0]
                        center_y += rect[1]

                    best_match = (center_x, center_y)

            if best_match:
                print(f"✅ Template match: {template_path} (confidence: {best_val:.2f})")

            return best_match

        except Exception as e:
            print(f"Template matching hiba: {e}")
            return None

    @staticmethod
    def capture_button_template(x, y, width=80, height=80, output_path=None):
        """
        Gombot befoglaló template capture

        Wizard használatra: egy gomb körül screenshot-ot készít

        Args:
            x, y: Gomb középpontja
            width, height: Template mérete (default: 80x80)
            output_path: Mentési útvonal (ha None, akkor visszaadja a képet)

        Returns:
            numpy.ndarray: Captured template vagy None
        """
        try:
            # Régió számítása (középpont körül)
            rect = WindowManager.get_window_rect()
            if not rect:
                print("❌ Ablak nem található")
                return None

            # Relatív koordináták az ablakon belül
            x_rel = x - rect[0]
            y_rel = y - rect[1]

            # Template régió (középpont körül)
            x1 = max(0, x_rel - width // 2)
            y1 = max(0, y_rel - height // 2)
            x2 = x1 + width
            y2 = y1 + height

            # Screenshot
            screen = ImageManager.screenshot()
            if screen is None:
                return None

            # Crop
            template = screen[y1:y2, x1:x2]

            # Mentés
            if output_path:
                cv2.imwrite(output_path, template)
                print(f"✅ Template mentve: {output_path}")

            return template

        except Exception as e:
            print(f"Template capture hiba: {e}")
            return None
    
    @staticmethod
    def read_text_from_region(region, debug_save=False, use_easyocr=True):
        """
        OCR szöveg kiolvasás - ML-ENHANCED VERZIÓ

        Többféle OCR módszert próbál:
        1. EasyOCR (ML-alapú, ha elérhető) - ELSŐDLEGES
        2. Tesseract + preprocessing (OTSU, Adaptive, CLAHE) - FALLBACK

        Args:
            region: dict - OCR régió
            debug_save: bool - Ha True, menti a feldolgozott képet hibakereséshez
            use_easyocr: bool - Ha True, EasyOCR-t próbál először (default)

        Returns:
            str: OCR szöveg
        """
        try:
            # Screenshot a régióból
            x, y, w, h = region['x'], region['y'], region['width'], region['height']

            # Teljes képernyő screenshot
            img = ImageGrab.grab()

            # Kivágás
            cropped = img.crop((x, y, x + w, y + h))

            # ===== DEBUG SAVE: EREDETI SCREENSHOT =====
            if debug_save:
                import datetime
                from pathlib import Path
                debug_dir = Path(__file__).parent / 'logs' / 'ocr_debug'
                debug_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                # Eredeti screenshot mentése (COLOR)
                cropped.save(str(debug_dir / f"ocr_{timestamp}_0_original.png"))
                print(f"  📸 Original screenshot: {debug_dir}/ocr_{timestamp}_0_original.png")
            # ============================================

            # Grayscale
            gray = cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2GRAY)

            # ===== ELSŐDLEGES: EasyOCR (ML-alapú) =====
            if EASYOCR_AVAILABLE and use_easyocr:
                try:
                    # Lazy load EasyOCR reader
                    global _easyocr_reader
                    if _easyocr_reader is None:
                        print("🔄 EasyOCR inicializálása (csak egyszer)...")
                        _easyocr_reader = easyocr.Reader(['en'], gpu=False)
                        print("✅ EasyOCR kész")

                    # EasyOCR futtatása
                    results = _easyocr_reader.readtext(gray, detail=0)

                    if results:
                        # Összes szöveg összefűzése
                        easyocr_text = " ".join(results).strip()

                        if easyocr_text:
                            if debug_save:
                                print(f"  🤖 EasyOCR: '{easyocr_text}'")
                            return easyocr_text

                except Exception as e:
                    print(f"⚠️  EasyOCR hiba: {e}, Tesseract fallback...")

            # ===== FALLBACK: Tesseract + Preprocessing =====

            # MÓDSZER 1: OTSU Threshold
            _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text1 = pytesseract.image_to_string(thresh1, config='--psm 7').strip()

            # MÓDSZER 2: Adaptive Threshold
            thresh2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, 11, 2)
            text2 = pytesseract.image_to_string(thresh2, config='--psm 7').strip()

            # MÓDSZER 3: Kontrasztfokozás + OTSU
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            _, thresh3 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text3 = pytesseract.image_to_string(thresh3, config='--psm 7').strip()

            # Debug save
            if debug_save:
                import datetime
                from pathlib import Path
                debug_dir = Path(__file__).parent / 'logs' / 'ocr_debug'
                debug_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                cv2.imwrite(str(debug_dir / f"ocr_{timestamp}_1_otsu.png"), thresh1)
                cv2.imwrite(str(debug_dir / f"ocr_{timestamp}_2_adaptive.png"), thresh2)
                cv2.imwrite(str(debug_dir / f"ocr_{timestamp}_3_clahe.png"), thresh3)
                print(f"  📸 Debug képek: {debug_dir}")

            # Válasszuk ki a leghosszabb valid szöveget
            results = [
                (text1, len(text1)),
                (text2, len(text2)),
                (text3, len(text3))
            ]

            valid_results = [(t, l) for t, l in results if l > 0]

            if valid_results:
                best_text = max(valid_results, key=lambda x: x[1])[0]
                if debug_save:
                    print(f"  📝 Tesseract best: '{best_text}'")
                return best_text
            else:
                return ""

        except Exception as e:
            print(f"OCR hiba: {e}")
            return ""


def safe_click(coords):
    """Biztonságos kattintás"""
    if coords:
        try:
            pyautogui.click(coords[0], coords[1])
            return True
        except:
            return False
    return False


def press_key(key):
    """Billentyű lenyomása"""
    try:
        key_map = {
            'space': Key.space,
            'enter': Key.enter,
            'esc': Key.esc,
            'f': 'f',
            'b': 'b',
            'tab': Key.tab
        }
        
        if key.lower() in key_map:
            mapped_key = key_map[key.lower()]
            if isinstance(mapped_key, str):
                keyboard.press(mapped_key)
                keyboard.release(mapped_key)
            else:
                keyboard.press(mapped_key)
                keyboard.release(mapped_key)
        else:
            keyboard.press(key)
            keyboard.release(key)
        
        return True
    except Exception as e:
        print(f"Billentyű hiba: {e}")
        return False


def wait_random(min_sec=3, max_sec=8):
    """Random várakozás (emberi faktor)"""
    delay = random.uniform(min_sec, max_sec)
    return delay


def is_garbage_ocr_text(text):
    """
    Ellenőrzi hogy az OCR szöveg "szemét-e" (popup/rossz képernyő)

    Példák rossz szövegekre:
    - 'Wi} 2' (helyett: '95%')
    - 'King's' (helyett: 'Ancient')
    - 'iim' (helyett: 'Ruins')
    - 'TS Un &' (random karakterek)
    - 'Wh ne' (szétszakadt szavak)

    Args:
        text: OCR szöveg

    Returns:
        bool: True ha szemét szöveg (popup valószínű)
    """
    if not text or len(text.strip()) < 2:
        return True

    import re
    text = text.strip()

    # Ismert szemét minták (a logokból)
    garbage_patterns = [
        r'Wi\}\s*\d',        # 'Wi} 2'
        r"King'?s",          # "King's"
        r'^iim$',            # 'iim'
        r'[A-Z]{1,2}\s+[A-Z][a-z]\s+[&\$#@]',  # 'TS Un &'
        r'Wh\s+ne',          # 'Wh ne'
        r'^[a-z]{2,3}$',     # Túl rövid lowercase szavak (pl 'iim')
    ]

    for pattern in garbage_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # Ha túl sok speciális karakter van
    special_chars = sum(1 for c in text if c in r'{}[]()<>~`!@#$%^&*_+=|\\')
    if special_chars > len(text) * 0.3:  # 30%+ speciális karakter
        return True

    return False


def find_and_close_popups(search_region=None, max_attempts=3, threshold=0.7):
    """
    X gomb keresése és automatikus kattintás (popup bezárás)

    HASZNÁLAT:
    - OCR előtt hívjuk meg, ha szemét szöveget olvas
    - Megpróbálja megtalálni az X gombot (close button)
    - Ha talál, rákattint és bezárja a popup-ot

    Args:
        search_region: dict - Keresési régió {'x', 'y', 'width', 'height'}
                             Ha None, akkor teljes képernyő
        max_attempts: int - Max próbálkozások száma
        threshold: float - Template matching threshold (0.7 = 70% egyezés)

    Returns:
        bool: True ha zárt be valamit, False ha nem talált semmit
    """
    from pathlib import Path

    # X gomb template fájlok keresése
    images_dir = Path(__file__).parent / 'images'
    x_templates = [
        images_dir / 'close_x.png',
        images_dir / 'x_button.png',
        images_dir / 'popup_close.png'
    ]

    # Válasszuk ki az első létező template-et
    x_template = None
    for template_path in x_templates:
        if template_path.exists():
            x_template = str(template_path)
            break

    if not x_template:
        # Nincs template, nem tudunk X gombot keresni
        return False

    print(f"[Popup Close] X gomb keresése: {Path(x_template).name}")

    for attempt in range(1, max_attempts + 1):
        print(f"[Popup Close] Próbálkozás {attempt}/{max_attempts}...")

        # Template matching (régió alapú, ha van megadva)
        coords = ImageManager.find_image(x_template, threshold=threshold, search_region=search_region)

        if coords:
            print(f"[Popup Close] ✓ X gomb megtalálva → {coords}")

            # Kattintás az X gombra
            time.sleep(0.3)
            safe_click(coords)

            print(f"[Popup Close] ✓ Popup bezárva")
            time.sleep(0.5)  # Rövid várakozás a bezárás után

            return True
        else:
            print(f"[Popup Close] X gomb nem található (attempt {attempt}/{max_attempts})")
            time.sleep(0.3)

    print(f"[Popup Close] Nincs popup ({max_attempts} próba)")
    return False


def get_screen_center():
    """Képernyő középpont számítása"""
    width, height = pyautogui.size()
    return (width // 2, height // 2)


def initialize_game_window(window_title="BlueStacks"):
    """Játék ablak inicializálása"""
    global game_window_title
    game_window_title = window_title
    
    if WindowManager.find_window(window_title):
        WindowManager.focus_window()
        return True
    return False