"""
ROK Auto Farm - Library
Alapvető függvények a meglévő library alapján
FIXED: WindowManager.find_window() exception handling
"""
import time
import random
import pyautogui
import cv2
import numpy as np
import pytesseract
from PIL import ImageGrab
import win32gui
import win32con
from pynput.keyboard import Controller, Key

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
    def find_image(template_path, threshold=0.7):
        """Template matching"""
        try:
            # Template betöltése
            template = cv2.imread(template_path)
            if template is None:
                return None
            
            # Screenshot
            screen = ImageManager.screenshot()
            if screen is None:
                return None
            
            # Matching
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                # Relatív → Abszolút koordináták
                rect = WindowManager.get_window_rect()
                if rect:
                    center_x += rect[0]
                    center_y += rect[1]
                
                return (center_x, center_y)
            
            return None
        except Exception as e:
            print(f"Template matching hiba: {e}")
            return None
    
    @staticmethod
    def read_text_from_region(region, debug_save=False):
        """
        OCR szöveg kiolvasás - JAVÍTOTT VERZIÓ

        Többféle preprocessing módszert próbál:
        1. OTSU threshold (eredeti)
        2. Adaptive threshold (jobb éjszaka)
        3. Kontrasztfokozás + OTSU

        Args:
            region: dict - OCR régió
            debug_save: bool - Ha True, menti a feldolgozott képet hibakereséshez

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

            # Grayscale
            gray = cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2GRAY)

            # ===== MÓDSZER 1: OTSU Threshold (eredeti) =====
            _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text1 = pytesseract.image_to_string(thresh1, config='--psm 7').strip()

            # ===== MÓDSZER 2: Adaptive Threshold (jobb sötétben) =====
            thresh2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, 11, 2)
            text2 = pytesseract.image_to_string(thresh2, config='--psm 7').strip()

            # ===== MÓDSZER 3: Kontrasztfokozás + OTSU =====
            # CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            _, thresh3 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text3 = pytesseract.image_to_string(thresh3, config='--psm 7').strip()

            # Debug save (ha kell)
            if debug_save:
                import datetime
                from pathlib import Path
                debug_dir = Path(__file__).parent / 'logs' / 'ocr_debug'
                debug_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                cv2.imwrite(str(debug_dir / f"ocr_{timestamp}_1_otsu.png"), thresh1)
                cv2.imwrite(str(debug_dir / f"ocr_{timestamp}_2_adaptive.png"), thresh2)
                cv2.imwrite(str(debug_dir / f"ocr_{timestamp}_3_clahe.png"), thresh3)

            # Válasszuk ki a leghosszabb valid szöveget (általában az a jó)
            results = [
                (text1, len(text1)),
                (text2, len(text2)),
                (text3, len(text3))
            ]

            # Szűrjük az üreseket
            valid_results = [(t, l) for t, l in results if l > 0]

            if valid_results:
                # Leghosszabb
                best_text = max(valid_results, key=lambda x: x[1])[0]
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