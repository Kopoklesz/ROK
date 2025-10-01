"""
Akciók végrehajtása - kattintások, gépelés, navigáció
"""
import time
import random
import pyautogui
from pynput.keyboard import Controller, Key
from typing import Tuple, Optional

from config.settings import (
    ACTION_DELAY_MIN,
    ACTION_DELAY_MAX,
    DEBUG_MODE
)


class ActionExecutor:
    """Játék akciók végrehajtása"""
    
    def __init__(self, window_manager, image_manager):
        self.window_mgr = window_manager
        self.image_mgr = image_manager
        self.keyboard = Controller()
        
        # pyautogui biztonság
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def click(self, coords: Tuple[int, int], clicks: int = 1, 
             button: str = 'left', ensure_focus: bool = True) -> bool:
        """
        Kattintás koordinátára
        
        Args:
            coords: (x, y) abszolút képernyő koordináták
            clicks: Kattintások száma
            button: 'left', 'right', 'middle'
            ensure_focus: Ablak fókuszálás előtte
            
        Returns:
            bool: Sikeres volt-e
        """
        if not coords:
            print("⚠️ Érvénytelen koordináták")
            return False
        
        x, y = coords
        
        # Fókusz biztosítása
        if ensure_focus:
            if not self.window_mgr.focus_window():
                print("⚠️ Ablak fókuszálás sikertelen")
                return False
            time.sleep(0.1)
        
        try:
            pyautogui.click(x, y, clicks=clicks, button=button)
            
            if DEBUG_MODE:
                print(f"🖱️ Kattintás: ({x}, {y}), button={button}, clicks={clicks}")
            
            self._random_delay()
            return True
        
        except Exception as e:
            print(f"❌ Kattintás hiba: {e}")
            return False
    
    def click_template(self, template_path: str, region: Optional[Tuple] = None,
                      clicks: int = 1, button: str = 'left') -> bool:
        """
        Template keresése és rákattintás
        
        Returns:
            bool: Sikeres volt-e (megtalálta és rákattintott)
        """
        coords = self.image_mgr.find_template(template_path, region)
        
        if coords:
            return self.click(coords, clicks, button)
        
        if DEBUG_MODE:
            print(f"⚠️ Template nem található: {template_path}")
        
        return False
    
    def drag(self, start_coords: Tuple[int, int], end_coords: Tuple[int, int],
            duration: float = 0.5) -> bool:
        """
        Drag művelet
        
        Args:
            start_coords: Kezdő pont (x, y)
            end_coords: Vég pont (x, y)
            duration: Húzás időtartama másodpercben
        """
        if not start_coords or not end_coords:
            return False
        
        self.window_mgr.focus_window()
        time.sleep(0.1)
        
        try:
            pyautogui.moveTo(start_coords[0], start_coords[1])
            time.sleep(0.1)
            pyautogui.drag(
                end_coords[0] - start_coords[0],
                end_coords[1] - start_coords[1],
                duration=duration
            )
            
            if DEBUG_MODE:
                print(f"🖱️ Drag: {start_coords} → {end_coords}")
            
            self._random_delay()
            return True
        
        except Exception as e:
            print(f"❌ Drag hiba: {e}")
            return False
    
    def type_text(self, text: str, interval: float = 0.05) -> bool:
        """
        Szöveg begépelése
        
        Args:
            text: Begépelendő szöveg
            interval: Karakterek közötti várakozás
        """
        self.window_mgr.focus_window()
        time.sleep(0.1)
        
        try:
            pyautogui.typewrite(text, interval=interval)
            
            if DEBUG_MODE:
                print(f"⌨️ Gépelés: {text}")
            
            self._random_delay()
            return True
        
        except Exception as e:
            print(f"❌ Gépelés hiba: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """
        Billentyű lenyomása
        
        Args:
            key: 'space', 'enter', 'esc', 'tab', stb.
        """
        self.window_mgr.focus_window()
        time.sleep(0.1)
        
        try:
            # pynput key mapping
            key_map = {
                'space': Key.space,
                'enter': Key.enter,
                'esc': Key.esc,
                'tab': Key.tab,
                'backspace': Key.backspace,
                'delete': Key.delete,
                'up': Key.up,
                'down': Key.down,
                'left': Key.left,
                'right': Key.right
            }
            
            if key.lower() in key_map:
                self.keyboard.press(key_map[key.lower()])
                self.keyboard.release(key_map[key.lower()])
            else:
                # Egyszerű karakter
                self.keyboard.press(key)
                self.keyboard.release(key)
            
            if DEBUG_MODE:
                print(f"⌨️ Billentyű: {key}")
            
            self._random_delay()
            return True
        
        except Exception as e:
            print(f"❌ Billentyű hiba: {e}")
            return False
    
    def wait(self, duration: float = 1.0):
        """Várakozás"""
        if DEBUG_MODE:
            print(f"⏳ Várakozás: {duration:.2f}s")
        time.sleep(duration)
    
    def navigate_to_building(self, building_type: str) -> bool:
        """
        Navigálás egy épülethez
        
        Args:
            building_type: 'barracks', 'archery', 'stable', 'siege'
        """
        template_map = {
            'barracks': 'buildings/barracks_icon.png',
            'archery': 'buildings/archery_icon.png',
            'stable': 'buildings/stable_icon.png',
            'siege': 'buildings/siege_icon.png'
        }
        
        template = template_map.get(building_type)
        if not template:
            print(f"⚠️ Ismeretlen épület típus: {building_type}")
            return False
        
        # 1. Keresés a városban (látható-e)
        coords = self.image_mgr.find_template(template)
        if coords:
            return self.click(coords)
        
        # 2. Ha nem látható, próbálj navigálni
        # Vissza a városba (ESC billentyű vagy fix koordináta)
        self.press_key('esc')
        time.sleep(0.5)
        
        # Újra keresés
        coords = self.image_mgr.find_template(template)
        if coords:
            return self.click(coords)
        
        print(f"⚠️ Épület nem található: {building_type}")
        return False
    
    def set_training_quantity(self, quantity: int) -> bool:
        """
        Képzési mennyiség beállítása
        
        Args:
            quantity: Egységek száma (-1 = max)
        """
        # Keresés quantity input field
        # Ez játéktól függ, implementálni kell a tényleges UI alapján
        
        if quantity == -1:
            # MAX gomb keresése
            if self.click_template('ui/max_button.png'):
                return True
        
        # Alternatíva: kattintás az input mezőre és gépelés
        input_field = self.image_mgr.find_template('ui/quantity_input.png')
        if input_field:
            self.click(input_field)
            time.sleep(0.2)
            
            # Előző érték törlése
            self.press_key('backspace')
            self.press_key('backspace')
            self.press_key('backspace')
            self.press_key('backspace')
            
            # Új érték
            self.type_text(str(quantity))
            return True
        
        print("⚠️ Mennyiség beállítás sikertelen")
        return False
    
    def emergency_escape(self) -> bool:
        """
        Vészhelyzeti kilépés (pl. elakadt UI)
        """
        if DEBUG_MODE:
            print("🚨 Emergency escape")
        
        # ESC többször
        for _ in range(3):
            self.press_key('esc')
            time.sleep(0.3)
        
        return True
    
    def _random_delay(self):
        """Random várakozás akciók között (humán-szerű viselkedés)"""
        delay = random.uniform(ACTION_DELAY_MIN, ACTION_DELAY_MAX)
        time.sleep(delay)


if __name__ == "__main__":
    # Teszt
    from core.window_manager import WindowManager
    from core.image_manager import ImageManager
    
    wm = WindowManager()
    if wm.find_window("BlueStacks"):
        wm.focus_window()
        
        im = ImageManager(wm)
        ae = ActionExecutor(wm, im)
        
        # Teszt kattintás
        coords = im.find_template("ui/train_button.png")
        if coords:
            ae.click(coords)