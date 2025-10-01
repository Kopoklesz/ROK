"""
Template Collector - Képek gyűjtése a játékból
"""
import cv2
import numpy as np
from pathlib import Path
import time
from pynput import mouse, keyboard

from core.window_manager import WindowManager
from core.image_manager import ImageManager
from config.settings import TEMPLATES_DIR, GAME_WINDOW_TITLE


class TemplateCollector:
    """
    Interaktív template gyűjtő tool
    """
    
    def __init__(self):
        print("="*60)
        print("🖼️  TEMPLATE COLLECTOR TOOL")
        print("="*60)
        
        self.window_mgr = WindowManager(GAME_WINDOW_TITLE)
        self.image_mgr = ImageManager(self.window_mgr)
        
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        
        if not self.window_mgr.find_window():
            raise RuntimeError("❌ Játék ablak nem található!")
        
        self.window_mgr.focus_window()
        
        print("\n✅ Template Collector inicializálva")
        print("\nHASZNÁLAT:")
        print("  1. Válaszd ki a képernyő területét egérrel")
        print("  2. Nyomd meg ENTER-t a mentéshez")
        print("  3. Nyomd meg ESC-et a kilépéshez")
        print("="*60 + "\n")
    
    def collect_interactive(self):
        """
        Interaktív gyűjtés - képernyő kijelölés egérrel
        """
        templates_to_collect = [
            # Buildings
            ('buildings/barracks_icon.png', 'Barracks ikon'),
            ('buildings/archery_icon.png', 'Archery Range ikon'),
            ('buildings/stable_icon.png', 'Stable ikon'),
            ('buildings/siege_icon.png', 'Siege Workshop ikon'),
            
            # UI elemek
            ('ui/train_button.png', 'Train gomb'),
            ('ui/train_menu_header.png', 'Train menü fejléc'),
            ('ui/zzzz_icon.png', 'Zzzz (busy queue) ikon'),
            ('ui/confirm_button.png', 'Confirm gomb'),
            ('ui/close_button.png', 'Close/X gomb'),
            ('ui/quantity_slider.png', 'Quantity slider'),
            ('ui/training_progress.png', 'Training progress bar'),
            
            # Tiers
            ('tiers/tier_t1.png', 'T1 tier ikon'),
            ('tiers/tier_t2.png', 'T2 tier ikon'),
            ('tiers/tier_t3.png', 'T3 tier ikon'),
            ('tiers/tier_t4.png', 'T4 tier ikon'),
            ('tiers/tier_t5.png', 'T5 tier ikon'),
        ]
        
        for template_path, description in templates_to_collect:
            print(f"\n{'='*60}")
            print(f"📸 Következő: {description}")
            print(f"   Mentés helye: {template_path}")
            print(f"{'='*60}")
            
            input("Nyomj ENTER-t a folytatáshoz...")
            
            # Képernyőkép
            self.window_mgr.focus_window()
            time.sleep(0.5)
            
            screenshot = self.image_mgr.screenshot()
            
            if screenshot is None:
                print("❌ Screenshot hiba!")
                continue
            
            # Területkijelölés
            region = self._select_region_gui(screenshot, description)
            
            if region is None:
                print("⚠️ Kihagyva")
                continue
            
            # Kivágás és mentés
            x, y, w, h = region
            cropped = screenshot[y:y+h, x:x+w]
            
            # Mentés
            full_path = TEMPLATES_DIR / template_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            cv2.imwrite(str(full_path), cropped)
            print(f"✅ Mentve: {full_path}")
            print(f"   Méret: {w}x{h} pixel")
        
        print("\n" + "="*60)
        print("✅ Template gyűjtés befejezve!")
        print(f"   Összes template: {len(templates_to_collect)}")
        print(f"   Hely: {TEMPLATES_DIR}")
        print("="*60)
    
    def _select_region_gui(self, screenshot, title):
        """
        Terület kijelölése GUI-val
        """
        clone = screenshot.copy()
        window_name = f"Jelöld ki: {title} (ENTER=mentés, ESC=mégsem)"
        
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, clone)
        
        # Mouse callback
        def mouse_callback(event, x, y, flags, param):
            nonlocal clone
            
            if event == cv2.EVENT_LBUTTONDOWN:
                self.selection_start = (x, y)
                self.selecting = True
            
            elif event == cv2.EVENT_MOUSEMOVE and self.selecting:
                clone = screenshot.copy()
                cv2.rectangle(clone, self.selection_start, (x, y), (0, 255, 0), 2)
                cv2.imshow(window_name, clone)
            
            elif event == cv2.EVENT_LBUTTONUP:
                self.selection_end = (x, y)
                self.selecting = False
                cv2.rectangle(clone, self.selection_start, self.selection_end, (0, 255, 0), 2)
                cv2.imshow(window_name, clone)
        
        cv2.setMouseCallback(window_name, mouse_callback)
        
        # Várakozás ENTER vagy ESC-re
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 13:  # ENTER
                cv2.destroyWindow(window_name)
                
                if self.selection_start and self.selection_end:
                    x1, y1 = self.selection_start
                    x2, y2 = self.selection_end
                    
                    x = min(x1, x2)
                    y = min(y1, y2)
                    w = abs(x2 - x1)
                    h = abs(y2 - y1)
                    
                    return (x, y, w, h)
                else:
                    return None
            
            elif key == 27:  # ESC
                cv2.destroyWindow(window_name)
                return None
    
    def collect_click_coordinates(self):
        """
        Koordináták gyűjtése kattintással
        """
        print("\n" + "="*60)
        print("🖱️  KOORDINÁTA GYŰJTÉS")
        print("="*60)
        print("\nKattints a játékban a fontos pontokra:")
        print("  - Város középpont")
        print("  - Épületek")
        print("  - Gombok")
        print("\nNyomj ESC-et a befejezéshez")
        print("="*60 + "\n")
        
        coordinates = {}
        
        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                name = input(f"\nKoordináta ({x}, {y}) neve: ").strip()
                if name:
                    coordinates[name] = (x, y)
                    print(f"✅ Mentve: {name} = ({x}, {y})")
        
        def on_press(key):
            if key == keyboard.Key.esc:
                return False  # Stop listener
        
        # Listeners
        mouse_listener = mouse.Listener(on_click=on_click)
        keyboard_listener = keyboard.Listener(on_press=on_press)
        
        mouse_listener.start()
        keyboard_listener.start()
        
        keyboard_listener.join()
        mouse_listener.stop()
        
        # Mentés JSON-ba
        import json
        coord_file = TEMPLATES_DIR / "coordinates.json"
        with open(coord_file, 'w') as f:
            json.dump(coordinates, f, indent=2)
        
        print(f"\n✅ Koordináták mentve: {coord_file}")
        print(f"   Összesen: {len(coordinates)} koordináta")


def main():
    collector = TemplateCollector()
    
    print("\nVÁLASSZ MÓDOT:")
    print("  1. Template képek gyűjtése (területkijelölés)")
    print("  2. Koordináták gyűjtése (kattintás)")
    print("  3. Mindkettő")
    
    choice = input("\nVálasztás (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        collector.collect_interactive()
    
    if choice in ['2', '3']:
        collector.collect_click_coordinates()


if __name__ == "__main__":
    main()