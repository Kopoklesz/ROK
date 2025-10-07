"""
ROK Auto Farm - Setup Wizard (Menu-Based v2.0)
ÚJ: March.png Template + March Detection Region
"""
import json
import cv2
import numpy as np
from pathlib import Path
from PIL import ImageGrab
from pynput import mouse, keyboard

from library import initialize_game_window
from utils.region_selector import RegionSelector


class SetupWizardMenu:
    """Setup wizard menürendszerrel"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent / 'config'
        self.images_dir = Path(__file__).parent / 'images'
        
        self.config_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        
        self.selector = RegionSelector()
    
    def run(self):
        """Főmenü indítása"""
        while True:
            self.show_main_menu()
            choice = self.get_menu_choice(0, 6)
            
            if choice == 0:
                print("\n✅ Kilépés a Setup Wizard-ból")
                break
            elif choice == 1:
                self.gathering_menu()
            elif choice == 2:
                self.training_menu()
            elif choice == 3:
                self.alliance_menu()
            elif choice == 4:
                self.anti_afk_menu()
            elif choice == 5:
                self.settings_menu()
            elif choice == 6:
                self.test_menu()
    
    def show_main_menu(self):
        """Főmenü megjelenítése"""
        print("\n" + "="*60)
        print("ROK AUTO FARM - SETUP WIZARD v2.0")
        print("="*60)
        print("\n1. 🌾 Gathering Setup")
        print("2. ⚔️  Training Setup")
        print("3. 🤝 Alliance Setup")
        print("4. 🔄 Anti-AFK Setup")
        print("5. ⚙️  Settings")
        print("6. ✅ Test & Verify (TODO)")
        print("0. Exit")
        print("\n" + "="*60)
    
    # ===== GATHERING MENU =====
    
    def gathering_menu(self):
        """Gathering setup almenü"""
        while True:
            print("\n" + "="*60)
            print("🌾 GATHERING SETUP")
            print("="*60)
            print("\n1. Resource Regions (wheat, wood, stone, gold OCR)")
            print("2. Time Regions (march_time, gather_time OCR)")
            print("3. Farm Coordinates")
            print("4. Gather.png Template")
            print("5. March.png Template")  # ÚJ
            print("6. March Detection Region")  # ÚJ
            print("0. Vissza")
            print("\n" + "="*60)
            
            choice = self.get_menu_choice(0, 6)
            
            if choice == 0:
                break
            elif choice == 1:
                self.setup_resource_regions()
            elif choice == 2:
                self.setup_time_regions()
            elif choice == 3:
                self.setup_farm_coordinates()
            elif choice == 4:
                self.setup_gather_template()
            elif choice == 5:
                self.setup_march_template()
            elif choice == 6:
                self.setup_march_detection_region()
    
    def setup_march_template(self):
        """March.png template (ÚJ)"""
        print("\n" + "="*60)
        print("📍 MARCH.PNG TEMPLATE SETUP")
        print("="*60)
        print("\nJelöld ki a 'march' szöveget vagy ikont!")
        print("(Ezt keresi a bot, hogy ellenőrizze van-e már commander úton)")
        
        march_path = self.images_dir / 'march.png'
        
        if march_path.exists():
            print(f"\nℹ️  Meglévő: {march_path}")
        
        if not self.wait_for_enter_or_esc("ENTER = új template"):
            return
        
        region = self.selector.select_region("MARCH ICON/TEXT")
        
        if region:
            screen = ImageGrab.grab()
            screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            cropped = screen_np[y:y+h, x:x+w]
            
            cv2.imwrite(str(march_path), cropped)
            print(f"\n✅ March template mentve: {march_path}")
        
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    def setup_march_detection_region(self):
        """March detekciós régió (ÚJ)"""
        print("\n" + "="*60)
        print("📍 MARCH DETECTION REGION SETUP")
        print("="*60)
        print("\nJelöld ki azt a területet, ahol a 'march' megjelenhet!")
        print("(Például a képernyő bal vagy jobb oldali sávja)")
        
        # Config betöltés
        gathering_file = self.config_dir / 'gathering_coords.json'
        if gathering_file.exists():
            with open(gathering_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Meglévő érték
        old_value = config.get('march_detection_region')
        if old_value:
            print(f"\nℹ️  Jelenlegi: {old_value}")
        else:
            print(f"\nℹ️  Nincs beállítva")
        
        if not self.wait_for_enter_or_esc("ENTER = új régió"):
            return
        
        region = self.selector.select_region("MARCH DETECTION REGION")
        
        if region:
            config['march_detection_region'] = region
            
            with open(gathering_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            print(f"\n✅ March detection region mentve")
        
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    # ... (további függvények változatlanul) ...
    
    def get_menu_choice(self, min_val, max_val):
        """Menüválasztás input validációval"""
        while True:
            try:
                choice = int(input(f"\nVálasztás ({min_val}-{max_val}): "))
                if min_val <= choice <= max_val:
                    return choice
                else:
                    print(f"❌ Érvénytelen választás! ({min_val}-{max_val} között)")
            except ValueError:
                print("❌ Számot adj meg!")
    
    def wait_for_enter_or_esc(self, message="ENTER = folytatás, ESC = skip"):
        """
        ENTER vagy ESC várakozás
        
        Returns:
            bool: True ha ENTER, False ha ESC
        """
        print(f"\n{message}")
        
        result = {'pressed': None}
        
        def on_press(key):
            if key == keyboard.Key.enter:
                result['pressed'] = 'enter'
                return False  # Stop listener
            elif key == keyboard.Key.esc:
                result['pressed'] = 'esc'
                return False  # Stop listener
        
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
        
        if result['pressed'] == 'enter':
            return True
        elif result['pressed'] == 'esc':
            print("⏩ Skip")
            return False
        
        return False


def main():
    """Main entry point"""
    print("="*60)
    print("ROK AUTO FARM - SETUP WIZARD")
    print("="*60)
    
    # Játék ablak inicializálás
    print("\nJáték ablak inicializálás...")
    if not initialize_game_window("BlueStacks"):
        print("❌ Játék ablak nem található!")
        print("Módosítsd a 'BlueStacks' szöveget a library.py-ban a játék ablak nevére.")
        return
    
    print("✅ Játék ablak OK\n")
    
    # Setup wizard indítás
    wizard = SetupWizardMenu()
    wizard.run()
    
    print("\n" + "="*60)
    print("Setup Wizard befejezve!")
    print("="*60)


if __name__ == "__main__":
    main()