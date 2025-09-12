import time
import cv2
import numpy as np
import pyautogui
import pytesseract
from typing import Optional, Tuple

# --- Tesseract beállítás (állítsd be a saját telepítési helyed szerint!) ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Template matching küszöb ---
TEMPLATE_THRESHOLD = 0.82


# ===== Segédfüggvény =====
def screenshot_to_cv(region=None):
    """Képernyőkép OpenCV formátumban"""
    im = pyautogui.screenshot(region=region) if region else pyautogui.screenshot()
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


# ===== Kép keresés fix próbálkozással =====
def find_image(image_path: str, retries: int = 5, delay: float = 1.0, region=None) -> Optional[Tuple[int,int]]:
    """Kép keresése meghatározott számú próbálkozással"""
    template = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if template is None:
        print(f"[HIBA] Nem találom a képet: {image_path}")
        return None
    th, tw = template.shape[:2]

    for attempt in range(retries):
        screen = screenshot_to_cv(region)
        res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val >= TEMPLATE_THRESHOLD:
            return (max_loc[0] + tw//2, max_loc[1] + th//2)
        time.sleep(delay)

    return None


# ===== Szöveg keresés fix próbálkozással =====
def find_text(word: str, retries: int = 5, delay: float = 1.0, region=None) -> Optional[Tuple[int,int]]:
    """Szöveg keresése meghatározott számú próbálkozással"""
    target = word.lower()
    for attempt in range(retries):
        screen = screenshot_to_cv(region)
        gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, lang='eng')

        for i, txt in enumerate(data['text']):
            if txt.strip().lower() == target:
                lx, ty, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                return (lx + w//2, ty + h//2)

        time.sleep(delay)

    return None


# ===== Kép keresés végtelen próbálkozással =====
def wait_for_image(image_path: str, delay: float = 1.0, region=None, max_loops: int = 1000):
    """Amíg nincs meg, addig próbálkozik (max_loops védelmi limit)"""
    for _ in range(max_loops):
        coords = find_image(image_path, retries=1, delay=delay, region=region)
        if coords:
            return coords
        time.sleep(delay)
    return None


# ===== Szöveg keresés végtelen próbálkozással =====
def wait_for_text(word: str, delay: float = 1.0, region=None, max_loops: int = 1000):
    """Amíg nincs meg, addig próbálkozik (max_loops védelmi limit)"""
    for _ in range(max_loops):
        coords = find_text(word, retries=1, delay=delay, region=region)
        if coords:
            return coords
        time.sleep(delay)
    return None


# ===== Kép keresés több backup képpel =====
def find_with_backups(*images, retries: int = 5, delay: float = 1.0, region=None) -> Optional[Tuple[int,int]]:
    """
    Több képet is megadhatsz (akár 2, akár 10 darabot).
    Sorban végigpróbálja őket, és ha valamelyiket megtalálja, visszaadja a koordinátát.
    Ha egyiket sem találja meg, None.
    """
    for img in images:
        print(f"Keresem: {img}")
        coords = find_image(img, retries=retries, delay=delay, region=region)
        if coords:
            print(f"Találtam: {img}")
            return coords
    print("Egyik backup kép sem található.")
    return None
