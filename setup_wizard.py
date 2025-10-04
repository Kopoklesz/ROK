"""
ROK Auto Farm - Setup Wizard
Teljes setup varázsló - első használat
"""
import json
import cv2
import numpy as np
from pathlib import Path
from PIL import ImageGrab

from library import initialize_game_window
from utils.region_selector import RegionSelector
from utils.coordinate_helper import CoordinateHelper
from pynput import mouse, keyboard


class SetupWizard:
    """Setup varázsló - minden beállítás"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent / 'config'
        self.images_dir = Path(__file__).parent / 'images'
        
        # Könyvtárak létrehozása
        self.config_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        
        self.selector = RegionSelector()
        self.current_coords = []
    
    def run(self):
        """Teljes setup folyamat"""
        print("="*60)
        print("🧙 ROK AUTO FARM - SETUP WIZARD")
        print("="*60)
        print("\nEz a varázsló végigvezet minden beállításon.")
        print("Az első használat után már nem kell futtatni!\n")
        print("="*60)
        
        input("\nNyomj ENTER-t a folytatáshoz...")
        
        # 1. Erőforrás régiók
        print("\n" + "="*60)
        print("1️⃣  ERŐFORRÁS SZÁMLÁLÓK BEÁLLÍTÁSA")
        print("="*60)
        farm_regions = self.setup_farm_regions()
        
        # 2. Idő régiók
        print("\n" + "="*60)
        print("2️⃣  IDŐ RÉGIÓK BEÁLLÍTÁSA")
        print("="*60)
        time_regions = self.setup_time_regions()
        
        # 3. Farm koordináták
        print("\n" + "="*60)
        print("3️⃣  FARM KOORDINÁTÁK BEÁLLÍTÁSA")
        print("="*60)
        farm_coords = self.setup_farm_coordinates(farm_regions)
        
        # 4. Gather.png template
        print("\n" + "="*60)
        print("4️⃣  GATHER GOMB TEMPLATE MENTÉSE")
        print("="*60)
        self.setup_gather_template()
        
        # 5. Settings létrehozása
        print("\n" + "="*60)
        print("5️⃣  ALAPÉRTELMEZETT BEÁLLÍTÁSOK")
        print("="*60)
        self.create_default_settings()
        
        # Befejezés
        print("\n" + "="*60)
        print("✅ SETUP BEFEJEZVE!")
        print("="*60)
        print("\nMost már futtathatod a farm_manager.py-t:")
        print("  python farm_manager.py")
        print("\n" + "="*60)
    
    def setup_farm_regions(self):
        """Erőforrás OCR régiók beállítása"""
        print("\nJelöld ki az erőforrás számokat a képernyőn!")
        print("Ha egy erőforrást nem akarsz használni, nyomd meg az ESC-et.\n")
        
        resources = ['wheat', 'wood', 'stone', 'gold']
        regions = {}
        
        for resource in resources:
            print(f"\n📍 {resource.upper()} erőforrás szám kijelölése...")
            input("  Nyomj ENTER-t a folytatáshoz...")
            
            region = self.selector.select_region(f"{resource.upper()} számláló")
            
            if region:
                regions[resource] = region
                print(f"  ✅ {resource.upper()} régió mentve: {region}")
            else:
                regions[resource] = None
                print(f"  ⚠️ {resource.upper()} kihagyva")
        
        # Mentés
        regions_file = self.config_dir / 'farm_regions.json'
        with open(regions_file, 'w', encoding='utf-8') as f:
            json.dump(regions, f, indent=2)
        
        print(f"\n✅ Erőforrás régiók mentve: {regions_file}")
        return regions
    
    def setup_time_regions(self):
        """Idő OCR régiók beállítása"""
        print("\nJelöld ki az idő megjelenítő területeket!")
        print("  - Idő A: Első idő (pl. march idő)")
        print("  - Idő B: Második idő (pl. gather idő)\n")
        
        time_regions = {}
        
        # Idő A
        print("\n📍 IDŐ A terület kijelölése...")
        input("  Nyomj ENTER-t a folytatáshoz...")
        region_a = self.selector.select_region("IDŐ A")
        time_regions['time_A'] = region_a
        print(f"  ✅ Idő A mentve: {region_a}")
        
        # Idő B
        print("\n📍 IDŐ B terület kijelölése...")
        input("  Nyomj ENTER-t a folytatáshoz...")
        region_b = self.selector.select_region("IDŐ B")
        time_regions['time_B'] = region_b
        print(f"  ✅ Idő B mentve: {region_b}")
        
        # Mentés
        time_file = self.config_dir / 'time_regions.json'
        with open(time_file, 'w', encoding='utf-8') as f:
            json.dump(time_regions, f, indent=2)
        
        print(f"\n✅ Idő régiók mentve: {time_file}")
        return time_regions
    
    def setup_farm_coordinates(self, farm_regions):
        """Farm koordináták beállítása"""
        print("\nFarm koordináták beállítása kattintással!")
        print("Minden farm típushoz 5 koordinátát kell megadni:\n")
        print("  1. Nyersanyag ikon (búza/fa/kő/arany gomb a térképen)")
        print("  2. Farm pozíció #1 (első farm helye)")
        print("  3. Farm pozíció #2 (második farm helye)")
        print("  4. Confirm/Send gomb")
        print("  5. Other (egyéb fix koordináta)\n")
        
        coord_names = [
            'resource_select',
            'farm_position_1',
            'farm_position_2',
            'confirm',
            'other'
        ]
        
        all_coords = {}
        
        # Csak azokhoz a farmokhoz kérjük a koordinátákat, amikhez van régió
        active_farms = [name for name, region in farm_regions.items() if region is not None]
        
        for farm_type in active_farms:
            print(f"\n{'='*60}")
            print(f"🌾 {farm_type.upper()} FARM KOORDINÁTÁK")
            print(f"{'='*60}")
            
            coords = {}
            
            for coord_name in coord_names:
                print(f"\n📍 {coord_name} koordináta beállítása...")
                print(f"   Kattints a játékban a megfelelő helyre!")
                
                coord = self.get_single_coordinate()
                coords[coord_name] = coord
                print(f"   ✅ {coord_name}: {coord}")
            
            all_coords[farm_type] = coords
        
        # Mentés
        coords_file = self.config_dir / 'farm_coords.json'
        with open(coords_file, 'w', encoding='utf-8') as f:
            json.dump(all_coords, f, indent=2)
        
        print(f"\n✅ Farm koordináták mentve: {coords_file}")
        return all_coords
    
    def get_single_coordinate(self):
        """Egyetlen koordináta bekérése kattintással"""
        coord = [None]
        
        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                coord[0] = [x, y]
                print(f"   🖱️ Koordináta: ({x}, {y})")
                return False  # Stop listener
        
        listener = mouse.Listener(on_click=on_click)
        listener.start()
        listener.join()
        
        return coord[0] if coord[0] else [0, 0]
    
    def setup_gather_template(self):
        """Gather.png template mentése"""
        print("\nGather gomb template mentése!")
        print("Jelöld ki a Gather gombot a képernyőn.\n")
        
        input("Nyomj ENTER-t a folytatáshoz...")
        
        region = self.selector.select_region("GATHER GOMB")
        
        if region:
            # Screenshot és kivágás
            screen = ImageGrab.grab()
            screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            cropped = screen_np[y:y+h, x:x+w]
            
            # Mentés
            gather_path = self.images_dir / 'gather.png'
            cv2.imwrite(str(gather_path), cropped)
            
            print(f"\n✅ Gather template mentve: {gather_path}")
            print(f"   Méret: {w}x{h} pixel")
        else:
            print("\n⚠️ Gather template kihagyva")
    
    def create_default_settings(self):
        """Alapértelmezett settings.json létrehozása"""
        settings = {
            "repeat_count": 4,
            "max_cycles": 100,
            "human_wait_min": 3,
            "human_wait_max": 8,
            "startup_wait_min": 20,
            "startup_wait_max": 25,
            "gather_retry_attempts": 25,
            "default_time_A": 60,
            "default_time_B": 5400
        }
        
        settings_file = self.config_dir / 'settings.json'
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        
        print("\n✅ Alapértelmezett beállítások:")
        for key, value in settings.items():
            print(f"   {key}: {value}")
        
        print(f"\n💾 Mentve: {settings_file}")


def main():
    """Main entry point"""
    
    # Játék ablak ellenőrzése
    if not initialize_game_window("BlueStacks"):  # Módosítsd!
        print("\n⚠️ Játék ablak nem található!")
        print("Indítsd el a játékot, majd futtasd újra a setup-ot.\n")
        return
    
    wizard = SetupWizard()
    wizard.run()


if __name__ == "__main__":
    main()