"""
Képfelismerés és OCR
"""
import cv2
import numpy as np
import pytesseract
import pyautogui
from PIL import Image, ImageGrab
from pathlib import Path
from typing import Optional, Tuple, List
import time

from config.settings import (
    TEMPLATE_MATCHING_THRESHOLD,
    TESSERACT_PATH,
    OCR_CONFIG,
    OCR_CONFIDENCE_THRESHOLD,
    TEMPLATES_DIR,
    SCREENSHOTS_DIR,
    DEBUG_MODE,
    SAVE_DEBUG_SCREENSHOTS
)

# Tesseract beállítása
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class ImageManager:
    """Képfelismerés és OCR kezelése"""
    
    def __init__(self, window_manager):
        self.window_mgr = window_manager
        self.template_cache = {}
        self.debug_counter = 0
        
    def screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Képernyőkép készítése
        
        Args:
            region: (x, y, width, height) vagy None (teljes ablak)
            
        Returns:
            numpy array (BGR formátum)
        """
        if region is None and self.window_mgr.window_handle:
            # Teljes játék ablak
            region = self.window_mgr.get_window_rect()
        
        try:
            img = pyautogui.screenshot(region=region)
            img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Debug mentés
            if SAVE_DEBUG_SCREENSHOTS and DEBUG_MODE:
                self._save_debug_screenshot(img_np)
            
            return img_np
        except Exception as e:
            print(f"❌ Screenshot hiba: {e}")
            return None
    
    def find_template(self, template_path: str, region: Optional[Tuple] = None, 
                     threshold: float = None) -> Optional[Tuple[int, int]]:
        """
        Template matching
        
        Args:
            template_path: Relatív útvonal (pl. "ui/train_button.png")
            region: Keresési terület (x, y, w, h)
            threshold: Egyezési küszöb (0-1)
            
        Returns:
            (x, y) abszolút koordináták vagy None
        """
        if threshold is None:
            threshold = TEMPLATE_MATCHING_THRESHOLD
        
        # Template betöltése
        template = self._load_template(template_path)
        if template is None:
            return None
        
        # Screenshot
        screen = self.screenshot(region)
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
            if region:
                center_x += region[0]
                center_y += region[1]
            elif self.window_mgr.window_handle:
                win_rect = self.window_mgr.get_window_rect()
                if win_rect:
                    center_x += win_rect[0]
                    center_y += win_rect[1]
            
            if DEBUG_MODE:
                print(f"✅ Template megtalálva: {template_path} @ ({center_x}, {center_y}), confidence={max_val:.2f}")
            
            return (center_x, center_y)
        
        if DEBUG_MODE:
            print(f"⚠️ Template nem található: {template_path}, max_confidence={max_val:.2f}")
        
        return None
    
    def find_all_templates(self, template_path: str, region: Optional[Tuple] = None,
                          threshold: float = None) -> List[Tuple[int, int]]:
        """
        Összes előfordulás keresése
        
        Returns:
            Lista koordináta tuple-ökből
        """
        if threshold is None:
            threshold = TEMPLATE_MATCHING_THRESHOLD
        
        template = self._load_template(template_path)
        if template is None:
            return []
        
        screen = self.screenshot(region)
        if screen is None:
            return []
        
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        h, w = template.shape[:2]
        coordinates = []
        
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + w // 2
            center_y = pt[1] + h // 2
            
            if region:
                center_x += region[0]
                center_y += region[1]
            elif self.window_mgr.window_handle:
                win_rect = self.window_mgr.get_window_rect()
                if win_rect:
                    center_x += win_rect[0]
                    center_y += win_rect[1]
            
            coordinates.append((center_x, center_y))
        
        return coordinates
    
    def extract_text(self, region: Tuple[int, int, int, int], 
                    config: str = None) -> str:
        """
        OCR szöveg kiolvasás
        
        Args:
            region: (x, y, width, height)
            config: Tesseract config string
            
        Returns:
            Kiolvasott szöveg
        """
        if config is None:
            config = OCR_CONFIG
        
        screen = self.screenshot(region)
        if screen is None:
            return ""
        
        try:
            # Előfeldolgozás (grayscale + threshold)
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR
            text = pytesseract.image_to_string(thresh, config=config)
            return text.strip()
        except Exception as e:
            print(f"❌ OCR hiba: {e}")
            return ""
    
    def extract_number(self, region: Tuple[int, int, int, int]) -> Optional[int]:
        """
        Szám kiolvasása OCR-rel
        
        Returns:
            int vagy None
        """
        text = self.extract_text(region, config='--psm 7 digits')
        
        # Csak számok megtartása
        digits = ''.join(filter(str.isdigit, text))
        
        if digits:
            try:
                return int(digits)
            except ValueError:
                pass
        
        return None
    
    def compare_screenshots(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Két kép különbségének mérése
        
        Returns:
            Difference score (0 = azonos, magasabb = nagyobb különbség)
        """
        if img1.shape != img2.shape:
            return float('inf')
        
        diff = cv2.absdiff(img1, img2)
        return np.sum(diff)
    
    def _load_template(self, template_path: str) -> Optional[np.ndarray]:
        """Template betöltése cache-ből vagy fájlból"""
        if template_path in self.template_cache:
            return self.template_cache[template_path]
        
        full_path = TEMPLATES_DIR / template_path
        
        if not full_path.exists():
            print(f"❌ Template nem található: {full_path}")
            return None
        
        template = cv2.imread(str(full_path))
        if template is None:
            print(f"❌ Template betöltési hiba: {full_path}")
            return None
        
        self.template_cache[template_path] = template
        return template
    
    def _save_debug_screenshot(self, img: np.ndarray):
        """Debug képernyőkép mentése"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = SCREENSHOTS_DIR / f"debug_{timestamp}_{self.debug_counter}.png"
        cv2.imwrite(str(filename), img)
        self.debug_counter += 1
        
        # Max 100 debug kép
        if self.debug_counter > 100:
            self.debug_counter = 0
    
    def clear_cache(self):
        """Template cache törlése"""
        self.template_cache.clear()


if __name__ == "__main__":
    # Teszt
    from core.window_manager import WindowManager
    
    wm = WindowManager()
    if wm.find_window("BlueStacks"):
        wm.focus_window()
        
        im = ImageManager(wm)
        screenshot = im.screenshot()
        print(f"Screenshot méret: {screenshot.shape}")
        
        # Template keresés teszt
        coords = im.find_template("ui/train_button.png")
        if coords:
            print(f"Train gomb: {coords}")