import time
import cv2
import numpy as np
import pyautogui
import pytesseract
import os
import glob
import ctypes
from typing import Optional, Tuple, List
from PIL import ImageGrab
import win32gui
import win32con
import win32api

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TEMPLATE_THRESHOLD = 0.6

# DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# -------------------- Ablakkezelés --------------------
class WindowManager:
    def __init__(self):
        self.game_window_handle = None
        self.game_window_title = None

    def find_game_window(self, partial_title=""):
        windows = []
        def enum_callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append((hwnd, title))
            return True
        win32gui.EnumWindows(enum_callback, None)

        for hwnd, title in windows:
            if partial_title.lower() in title.lower():
                self.game_window_handle = hwnd
                self.game_window_title = title
                print(f"✅ Játék ablak találva: {title}")
                return True

        print("🔎 Elérhető ablakok:")
        for i, (hwnd, title) in enumerate(windows):
            print(f"  {i + 1}. {title}")

        choice = input("Válassz ablak számot, ami a játék: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(windows):
                self.game_window_handle = windows[idx][0]
                self.game_window_title = windows[idx][1]
                print(f"✅ Kiválasztva: {self.game_window_title}")
                return True
        except:
            pass

        print("❌ Nem található a játék ablak!")
        return False

    def focus_game_window(self):
        if not self.game_window_handle:
            return False
        try:
            win32gui.ShowWindow(self.game_window_handle, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(self.game_window_handle)
            return True
        except:
            return False

    def get_window_rect(self) -> Optional[Tuple[int,int,int,int]]:
        if not self.game_window_handle:
            return None
        return win32gui.GetWindowRect(self.game_window_handle)

# -------------------- Többmonitor kezelés --------------------
class MultiMonitorManager:
    def __init__(self):
        self.monitors = self._detect_monitors()
        self.offset_x, self.offset_y = self._calc_offset()

    def _detect_monitors(self) -> list:
        monitors = []
        for monitor in win32api.EnumDisplayMonitors():
            info = win32api.GetMonitorInfo(monitor[0])
            r = info['Monitor']
            monitors.append((r[0], r[1], r[2]-r[0], r[3]-r[1]))
        return monitors if monitors else [(0,0,pyautogui.size().width, pyautogui.size().height)]

    def _calc_offset(self):
        min_x = min(m[0] for m in self.monitors)
        min_y = min(m[1] for m in self.monitors)
        return (-min_x if min_x < 0 else 0, -min_y if min_y < 0 else 0)

    def fix_coordinates(self, x, y):
        return x + self.offset_x, y + self.offset_y

    def get_monitor_regions(self):
        return self.monitors

# -------------------- Képkeresés --------------------
class ImageManager:
    def __init__(self, window_manager: WindowManager, monitor_manager: MultiMonitorManager):
        self.win_mgr = window_manager
        self.mon_mgr = monitor_manager

    def screenshot(self, region=None):
        if region is None and self.win_mgr.game_window_handle:
            region = self.win_mgr.get_window_rect()
        img = pyautogui.screenshot(region=region)
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    def find_image(self, template_path: str, region=None) -> Optional[Tuple[int,int]]:
        tpl = cv2.imread(template_path)
        if tpl is None:
            return None
        screen = self.screenshot(region)
        res = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val >= TEMPLATE_THRESHOLD:
            h, w = tpl.shape[:2]
            x, y = (max_loc[0]+w//2, max_loc[1]+h//2)
            if region:
                x += region[0]
                y += region[1]
            return self.mon_mgr.fix_coordinates(x, y)
        return None

# -------------------- Globális példányok --------------------
_window_manager = WindowManager()
_monitor_manager = MultiMonitorManager()
_image_manager = ImageManager(_window_manager, _monitor_manager)

# -------------------- Globális helper függvények --------------------
def safe_click(coords, clicks=1, button='left', ensure_focus=True):
    if not coords:
        print("⚠️ Érvénytelen koordináták a kattintáshoz")
        return False

    x, y = coords  # már ABSZOLÚT koordináták a képernyőn

    # Csak multi-monitor offset-et számoljuk
    x, y = _monitor_manager.fix_coordinates(x, y)

    # Fokusz a játék ablakra
    if ensure_focus and _window_manager.game_window_handle:
        _window_manager.focus_game_window()
        time.sleep(0.1)

    pyautogui.click(x, y, clicks=clicks, button=button)
    print(f"✅ Kattintás: ({x}, {y})")
    return True

def initialize_game_window(title_hint="BlueStacks App Player"):
    print("\n🎮 JÁTÉK ABLAK BEÁLLÍTÁSA")
    success = _window_manager.find_game_window(title_hint)
    if success:
        _window_manager.focus_game_window()
        rect = _window_manager.get_window_rect()
        if rect:
            print(f"📍 Ablak pozíció: x={rect[0]}, y={rect[1]}, w={rect[2]}, h={rect[3]}")
        return True
    print("❌ Nem található a játék ablak!")
    return False

def wait_for_image_forever(template_path: str, delay=1.0):
    while True:
        coords = _image_manager.find_image(template_path)
        if coords:
            return coords
        time.sleep(delay)
