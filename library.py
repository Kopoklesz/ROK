import time
import cv2
import numpy as np
import pyautogui
import pytesseract
import tkinter as tk
import os
import glob
import subprocess
import json
import re
from typing import Optional, Tuple, List
from PIL import ImageGrab

# --- KONFIGURÁCIÓS BEÁLLÍTÁSOK ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TEMPLATE_THRESHOLD = 0.6


# ===== MULTI-MONITOR MANAGER =====
class MultiMonitorManager:
    def __init__(self):
        self.monitors = self._detect_monitors()
        self.primary_monitor = self.monitors[0] if self.monitors else None
        print(f"🖥️  Detektált monitorok: {len(self.monitors)}")
        for i, monitor in enumerate(self.monitors):
            print(f"   Monitor {i + 1}: x={monitor[0]}, y={monitor[1]}, w={monitor[2]}, h={monitor[3]}")

    def _detect_monitors(self) -> List[Tuple[int, int, int, int]]:
        """Monitorok detektálása többféle módszerrel"""
        monitors = []

        try:
            # 1. Windows WMI lekérdezés
            result = subprocess.run([
                'powershell', '-Command',
                'Get-WmiObject -Class Win32_DesktopMonitor | Select-Object Name, ScreenWidth, ScreenHeight | ConvertTo-Json'
            ], capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                monitor_data = json.loads(result.stdout)
                if isinstance(monitor_data, dict):
                    monitor_data = [monitor_data]

                print(f"🖥️ WMI detektált {len(monitor_data)} monitor(t)")
                for i, monitor in enumerate(monitor_data):
                    if monitor.get('ScreenWidth') and monitor.get('ScreenHeight'):
                        width = int(monitor['ScreenWidth'])
                        height = int(monitor['ScreenHeight'])
                        x = i * width
                        monitors.append((x, 0, width, height))

        except Exception as e:
            print(f"⚠️ WMI módszer sikertelen: {e}")

        # 2. Fallback módszer
        if not monitors:
            root = tk.Tk()
            root.withdraw()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()

            full_size = pyautogui.size()

            if full_size.width > screen_width * 1.1:
                estimated_monitors = round(full_size.width / screen_width)
                monitor_width = full_size.width // estimated_monitors

                for i in range(estimated_monitors):
                    x = i * monitor_width
                    height = min(screen_height, full_size.height)
                    monitors.append((x, 0, monitor_width, height))
            else:
                monitors.append((0, 0, screen_width, screen_height))

        # 3. Végső fallback
        if not monitors:
            size = pyautogui.size()
            monitors.append((0, 0, size.width, size.height))

        return monitors

    def get_all_monitor_regions(self) -> List[Tuple[int, int, int, int]]:
        return self.monitors.copy()

    def is_multi_monitor(self) -> bool:
        return len(self.monitors) > 1


# Globális monitor manager
_monitor_manager = MultiMonitorManager()


# ===== ALAPVETŐ SEGÉDFÜGGVÉNYEK =====
def screenshot_to_cv(region=None):
    """Képernyőkép OpenCV formátumban"""
    im = pyautogui.screenshot(region=region) if region else pyautogui.screenshot()
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def fix_coordinates(coords):
    """Koordináta normalizálás - különböző típusok egységesítése"""
    if hasattr(coords, 'x') and hasattr(coords, 'y'):
        return (int(coords.x), int(coords.y))
    elif isinstance(coords, (tuple, list)) and len(coords) == 2:
        return (int(coords[0]), int(coords[1]))
    else:
        print(f"⚠️ Ismeretlen koordináta típus: {type(coords)}")
        return None


# ===== TEMPLATE KEZELÉS =====
def find_template_files(base_name: str, images_folder: str = "../images/") -> List[str]:
    """Automatikus template fájl keresés"""
    templates = []
    patterns = [f"{base_name}.png", f"{base_name}_*.png"]

    for pattern in patterns:
        search_path = os.path.join(images_folder, pattern)
        found_files = glob.glob(search_path)
        templates.extend(found_files)

    templates = sorted(list(set(templates)))

    if templates:
        print(f"🔍 Találtam {len(templates)} template-et {base_name}-hez:")
        for template in templates:
            print(f"   📁 {os.path.basename(template)}")

    return templates


def create_template_helper(farm_name: str, images_folder: str = "../images/"):
    """Template készítő segédprogram"""
    print(f"\n🎯 Template készítő - {farm_name}")
    print("1. Vidd az egeret a célpont fölé")
    print("2. Nyomj ENTER-t")

    input("ENTER-t nyomva...")

    try:
        pos = pyautogui.position()
        print(f"📍 Pozíció: {pos}")

        sizes = [60, 80, 100]
        for size in sizes:
            half_size = size // 2
            region = (pos.x - half_size, pos.y - half_size, size, size)

            screenshot = pyautogui.screenshot(region=region)
            filename = f"{farm_name}_{size}x{size}.png"
            filepath = os.path.join(images_folder, filename)

            os.makedirs(images_folder, exist_ok=True)
            screenshot.save(filepath)
            print(f"✅ {filename}")
    except Exception as e:
        print(f"❌ Hiba: {e}")


# ===== KÉPKERESÉS - TISZTÍTOTT VERZIÓ =====
def find_image_single_template(template_path: str, region: Tuple[int, int, int, int]) -> Optional[
    Tuple[int, int, float]]:
    """Egy template keresése egy régióban"""
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        return None

    try:
        screen = screenshot_to_cv(region)
        res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val >= TEMPLATE_THRESHOLD:
            th, tw = template.shape[:2]
            # Abszolút koordináták számítása
            global_x = region[0] + max_loc[0] + tw // 2
            global_y = region[1] + max_loc[1] + th // 2
            return (global_x, global_y, max_val)
    except Exception as e:
        print(f"⚠️ Template keresési hiba: {e}")

    return None


def find_image_multi_template_multi_monitor(template_files: List[str], retries: int = 5, delay: float = 1.0) -> \
Optional[Tuple[int, int, str]]:
    """Több template több monitoron - OPTIMALIZÁLT"""
    if not template_files:
        return None

    monitors = _monitor_manager.get_all_monitor_regions()
    print(f"🔍 Keresés: {len(template_files)} template × {len(monitors)} monitor")

    best_match = 0.0
    best_info = None

    for attempt in range(retries):
        print(f"🔄 Próbálkozás {attempt + 1}/{retries}")

        for template_path in template_files:
            template_name = os.path.basename(template_path)

            for i, region in enumerate(monitors):
                result = find_image_single_template(template_path, region)
                if result:
                    x, y, confidence = result
                    percentage = confidence * 100
                    print(f"   {template_name} @ Monitor {i + 1}: {percentage:.1f}%")

                    if percentage > best_match * 100:
                        best_match = confidence
                        best_info = (template_name, i + 1, (x, y), region)

                    if confidence >= TEMPLATE_THRESHOLD:
                        print(f"✅ TALÁLAT! {template_name} @ Monitor {i + 1}: ({x}, {y}), {percentage:.1f}%")
                        return (x, y, template_path)

        if attempt < retries - 1:
            time.sleep(delay)

    # Debug a legjobb egyezésről
    if best_info:
        template_name, monitor_num, coords, region = best_info
        print(f"❌ Legjobb egyezés: {template_name} @ Monitor {monitor_num}, {best_match * 100:.1f}%")

    return None


# ===== FŐSODRÓ KERESÉSI FÜGGVÉNYEK =====
def find_image(image_path: str, retries: int = 5, delay: float = 1.0, region=None) -> Optional[Tuple[int, int]]:
    """Képkeresés - egységesített interfész"""
    if region is not None:
        # Specifikus régióban keresés
        result = find_image_single_template(image_path, region)
        return (result[0], result[1]) if result else None
    else:
        # Automatikus multi-template + multi-monitor keresés
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        images_folder = os.path.dirname(image_path) + "/"
        template_files = find_template_files(base_name, images_folder)

        if not template_files:
            template_files = [image_path]

        result = find_image_multi_template_multi_monitor(template_files, retries, delay)
        return (result[0], result[1]) if result else None


def wait_for_image_forever(path: str, delay: float = 2, confidence: float = 0.3):
    """Végtelen képkeresés PyAutoGUI + saját rendszer kombinációval"""
    monitors = _monitor_manager.get_all_monitor_regions()

    # Template fájlok automatikus betöltése
    base_name = os.path.splitext(os.path.basename(path))[0]
    images_folder = os.path.dirname(path) + "/"
    template_files = find_template_files(base_name, images_folder)

    if not template_files:
        template_files = [path]

    print(f"🔍 Végtelen keresés: {len(template_files)} template, {len(monitors)} monitor")
    print(f"📊 Confidence küszöb: {confidence * 100:.1f}%")

    attempt_count = 0

    while True:
        attempt_count += 1
        found = False

        # Saját képkeresési rendszer próbája
        for template_path in template_files:
            for i, region in enumerate(monitors):
                result = find_image_single_template(template_path, region)
                if result:
                    x, y, match_confidence = result
                    template_name = os.path.basename(template_path)
                    print(f"✅ TALÁLAT! {template_name} @ Monitor {i + 1}, {attempt_count}. próbálkozás: ({x}, {y})")
                    return pyautogui.Point(x, y)

        # PyAutoGUI próbája (fallback)
        try:
            for template_path in template_files:
                for i, region in enumerate(monitors):
                    coords = pyautogui.locateCenterOnScreen(template_path, confidence=confidence, region=region)
                    if coords:
                        template_name = os.path.basename(template_path)
                        print(f"✅ PYAUTOGUI TALÁLAT! {template_name} @ Monitor {i + 1}: {coords}")
                        return coords
        except:
            pass

        # Progress report
        if attempt_count % 5 == 0:
            print(f"   #{attempt_count}: Keresés folytatódik...")

        time.sleep(delay)


def find_with_backups(*images, retries: int = 5, delay: float = 1.0, region=None) -> Optional[Tuple[int, int]]:
    """Backup képek keresése"""
    for img in images:
        print(f"🔍 Keresem: {img}")
        coords = find_image(img, retries=retries, delay=delay, region=region)
        if coords:
            print(f"✅ Találtam: {img}")
            return coords
    print("❌ Egyik kép sem található")
    return None


# ===== OCR FUNKCIÓK =====
def find_text_multi_monitor(word: str, retries: int = 5, delay: float = 1.0) -> Optional[Tuple[int, int]]:
    """Szövegkeresés OCR-rel több monitoron"""
    target = word.lower()
    monitors = _monitor_manager.get_all_monitor_regions()

    for attempt in range(retries):
        for i, region in enumerate(monitors):
            try:
                screen = screenshot_to_cv(region)
                gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
                data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, lang='eng')

                for j, txt in enumerate(data['text']):
                    if txt.strip().lower() == target:
                        lx, ty, w, h = data['left'][j], data['top'][j], data['width'][j], data['height'][j]
                        global_x = region[0] + lx + w // 2
                        global_y = region[1] + ty + h // 2
                        return (global_x, global_y)
            except Exception as e:
                print(f"⚠️ OCR hiba Monitor {i + 1}-en: {e}")
                continue
        time.sleep(delay)

    return None


def find_label_and_two_numbers(label: str, region=None):
    """Label és két szám keresése OCR-rel"""
    monitors = _monitor_manager.get_all_monitor_regions() if region is None else [region]

    for i, monitor_region in enumerate(monitors):
        try:
            screenshot = ImageGrab.grab(bbox=monitor_region)
            text = pytesseract.image_to_string(screenshot)
            lines = text.splitlines()

            for line in lines:
                if label.lower() in line.lower():
                    match = re.findall(r"([\d,]+)\s*\+\s*([\d,]+)", line)
                    if match:
                        base = int(match[0][0].replace(",", ""))
                        bonus = int(match[0][1].replace(",", ""))
                        print(f"✅ {label} találva Monitor {i + 1}-en: {base} + {bonus}")
                        return base, bonus
        except Exception as e:
            print(f"⚠️ OCR hiba Monitor {i + 1}-en: {e}")

    return None


# ===== SEGÉDFÜGGVÉNYEK =====
def calculate_fill_time(production, capacity):
    """Megtelési idő számítása"""
    prod_total = sum(production)
    cap_total = sum(capacity)
    if prod_total <= 0:
        return float("inf"), prod_total, cap_total
    hours_to_fill = cap_total / prod_total
    return int(hours_to_fill * 3600), prod_total, cap_total


def is_duplicate(coords, farm_list, tolerance=20):
    """Koordináta duplikáció ellenőrzés"""
    fixed_coords = fix_coordinates(coords)
    if not fixed_coords:
        return False

    for farm in farm_list:
        farm_coords = fix_coordinates(farm)
        if farm_coords:
            distance = ((fixed_coords[0] - farm_coords[0]) ** 2 + (fixed_coords[1] - farm_coords[1]) ** 2) ** 0.5
            if distance < tolerance:
                return True
    return False


# ===== DEBUG FUNKCIÓK =====
def debug_save_screenshots():
    """Debug screenshot készítés"""
    try:
        region = _monitor_manager.get_all_monitor_regions()[0]
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save("debug_monitor_1.png")
        print(f"📸 debug_monitor_1.png mentve")
    except Exception as e:
        print(f"❌ Screenshot hiba: {e}")


def debug_multi_monitor_info():
    """Multi-monitor debug információk"""
    print("\n=== MULTI-MONITOR DEBUG ===")
    manager = _monitor_manager
    print(f"Monitorok: {len(manager.monitors)}")
    print(f"Multi-monitor: {'IGEN' if manager.is_multi_monitor() else 'NEM'}")

    for i, region in enumerate(manager.monitors):
        print(f"Monitor {i + 1}: x={region[0]}, y={region[1]}, w={region[2]}, h={region[3]}")

    debug_save_screenshots()
    print("=== DEBUG VÉGE ===\n")


def debug_template_system():
    """Template rendszer debug"""
    print("\n=== TEMPLATE SYSTEM DEBUG ===")

    farm_types = ["stone_farm", "wheat_farm", "gold_farm", "wood_farm", "information_icon"]
    images_folder = "../images/"

    for farm_type in farm_types:
        templates = find_template_files(farm_type, images_folder)
        if templates:
            print(f"✅ {farm_type}: {len(templates)} template")
        else:
            print(f"❌ {farm_type}: Nincs template")

    print("=== TEMPLATE DEBUG VÉGE ===\n")


def interactive_template_creator():
    """Interaktív template készítő"""
    print("\n🎯 INTERAKTÍV TEMPLATE KÉSZÍTŐ")

    farm_types = {"1": "stone_farm", "2": "wheat_farm", "3": "gold_farm", "4": "wood_farm", "5": "information_icon"}

    while True:
        print("\nVálassz típust:")
        for key, farm in farm_types.items():
            print(f"  {key}. {farm}")
        print("  q. Kilépés")

        choice = input("\nVálasztás: ").strip().lower()

        if choice == 'q':
            break
        elif choice in farm_types:
            create_template_helper(farm_types[choice])
        else:
            print("❌ Érvénytelen választás")


# ===== FŐPROGRAM =====
if __name__ == "__main__":
    debug_multi_monitor_info()
    debug_template_system()

    create_templates = input("\nKészítsek template-eket? (y/N): ").strip().lower()
    if create_templates in ['y', 'yes']:
        interactive_template_creator()