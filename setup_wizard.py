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

        # 5. Explorer koordináták
        print("\n" + "="*60)
        print("5️⃣  EXPLORER KOORDINÁTÁK BEÁLLÍTÁSA")
        print("="*60)
        self.setup_explorer_coordinates()

        # 6. Settings létrehozása
        print("\n" + "="*60)
        print("6️⃣  ALAPÉRTELMEZETT BEÁLLÍTÁSOK")
        print("="*60)
        self.create_default_settings()
        
        # Befejezés
        print("\n" + "="*60)
        print("✅ SETUP BEFEJEZVE!")
        print("="*60)
        print("\nMost már futtathatod a farm_manager.py-t:")
        print("  python farm_manager.py")
        print("\n" + "="*60)
    
    def wait_for_enter_or_esc(self, prompt="ENTER = folytatás"):
        """Vár ENTER-re vagy ESC-re"""
        print(f"  {prompt}, ESC = kihagyás")
        
        cancelled = [False]
        
        def on_press(key):
            try:
                if key == keyboard.Key.enter:
                    return False  # Stop
                elif key == keyboard.Key.esc:
                    cancelled[0] = True
                    print(f"  ⏹️  ESC - Kihagyva")
                    return False  # Stop
            except:
                pass
        
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        listener.join()
        
        return not cancelled[0]  # True = ENTER, False = ESC
    
    def setup_farm_regions(self):
        """Erőforrás OCR régiók beállítása"""
        print("\nJelöld ki az erőforrás számokat a képernyőn!")
        print("ESC = megtartja a régi értéket (ha van)\n")
        
        resources = ['wheat', 'wood', 'stone', 'gold']
        
        # Meglévő régiók betöltése (ha vannak)
        regions_file = self.config_dir / 'farm_regions.json'
        if regions_file.exists():
            try:
                with open(regions_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        regions = json.loads(content)
                    else:
                        regions = {}
                print("ℹ️  Meglévő régiók betöltve. ESC = régi érték megtartása\n")
            except json.JSONDecodeError:
                print("⚠️ Hibás JSON, új régiók létrehozása...\n")
                regions = {}
        else:
            regions = {}
        
        for resource in resources:
            # Régi érték kiírása
            old_value = regions.get(resource)
            if old_value:
                print(f"\n📍 {resource.upper()} - Jelenlegi: {old_value}")
            else:
                print(f"\n📍 {resource.upper()} - Nincs beállítva")
            
            # Vár ENTER-re vagy ESC-re
            if not self.wait_for_enter_or_esc("ENTER = új érték"):
                # ESC = régi megtartása
                if old_value:
                    print(f"  ℹ️  {resource.upper()} régi érték megtartva")
                else:
                    regions[resource] = None
                    print(f"  ⚠️ {resource.upper()} kihagyva")
                continue
            
            region = self.selector.select_region(f"{resource.upper()} számláló")
            
            if region:
                regions[resource] = region
                print(f"  ✅ {resource.upper()} régió frissítve")
            else:
                if old_value:
                    print(f"  ℹ️  {resource.upper()} régi érték megtartva")
                else:
                    regions[resource] = None
                    print(f"  ⚠️ {resource.upper()} kihagyva")
        
        # Mentés
        with open(regions_file, 'w', encoding='utf-8') as f:
            json.dump(regions, f, indent=2)
        
        print(f"\n✅ Erőforrás régiók mentve: {regions_file}")
        return regions
    
    def setup_time_regions(self):
        """Idő OCR régiók beállítása"""
        print("\nJelöld ki az idő megjelenítő területeket!")
        print("  - March Time: March idő (első idő)")
        print("  - Gather Time: Gather idő (második idő)")
        print("ESC = megtartja a régi értéket (ha van)\n")
        
        # Meglévő régiók betöltése
        time_file = self.config_dir / 'time_regions.json'
        if time_file.exists():
            try:
                with open(time_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        time_regions = json.loads(content)
                    else:
                        time_regions = {}
                print("ℹ️  Meglévő idő régiók betöltve.\n")
            except json.JSONDecodeError:
                print("⚠️ Hibás JSON, új idő régiók létrehozása...\n")
                time_regions = {}
        else:
            time_regions = {}
        
        # March Time (Idő A)
        old_value_a = time_regions.get('march_time')
        if old_value_a:
            print(f"\n📍 MARCH TIME - Jelenlegi: {old_value_a}")
        else:
            print(f"\n📍 MARCH TIME - Nincs beállítva")
        
        if not self.wait_for_enter_or_esc("ENTER = új érték"):
            if old_value_a:
                print(f"  ℹ️  March Time régi érték megtartva")
            else:
                print(f"  ⚠️ March Time kihagyva")
        else:
            region_a = self.selector.select_region("MARCH TIME")
            if region_a:
                time_regions['march_time'] = region_a
                print(f"  ✅ March Time frissítve")
            else:
                if old_value_a:
                    print(f"  ℹ️  March Time régi érték megtartva")
                else:
                    print(f"  ⚠️ March Time kihagyva")
        
        # Gather Time (Idő B)
        old_value_b = time_regions.get('gather_time')
        if old_value_b:
            print(f"\n📍 GATHER TIME - Jelenlegi: {old_value_b}")
        else:
            print(f"\n📍 GATHER TIME - Nincs beállítva")
        
        if not self.wait_for_enter_or_esc("ENTER = új érték"):
            if old_value_b:
                print(f"  ℹ️  Gather Time régi érték megtartva")
            else:
                print(f"  ⚠️ Gather Time kihagyva")
        else:
            region_b = self.selector.select_region("GATHER TIME")
            if region_b:
                time_regions['gather_time'] = region_b
                print(f"  ✅ Gather Time frissítve")
            else:
                if old_value_b:
                    print(f"  ℹ️  Gather Time régi érték megtartva")
                else:
                    print(f"  ⚠️ Gather Time kihagyva")
        
        # Mentés
        with open(time_file, 'w', encoding='utf-8') as f:
            json.dump(time_regions, f, indent=2)
        
        print(f"\n✅ Idő régiók mentve: {time_file}")
        return time_regions
    
    def setup_farm_coordinates(self, farm_regions):
        """Farm koordináták beállítása"""
        print("\nFarm koordináták beállítása kattintással!")
        print("\n📋 FARM FOLYAMAT (helyes sorrend):")
        print("  1. Nyersanyag ikon")
        print("  2. Szint gomb")
        print("  3. Keresés gomb")
        print("  4. ⚫ HOLT KATTINTÁS (gather helyett - NEM mentődik)")
        print("  5. Új egység gomb")
        print("  6. March gomb")
        print("  7. Képernyő közepe")
        print("\nESC = kihagyás (régi érték megtartása)\n")
        
        coord_names = [
            'resource_icon',      # 1. Nyersanyag ikon
            'level_button',       # 2. Szint
            'search_button',      # 3. Keresés
            'dead_click',         # 4. HOLT KATTINTÁS (NEM mentődik)
            'new_troops',         # 5. Új egység
            'march_button',       # 6. March
            'screen_center'       # 7. Képernyő közepe
        ]
        
        coord_labels = {
            'resource_icon': 'Nyersanyag ikon',
            'level_button': 'Szint gomb',
            'search_button': 'Keresés gomb',
            'dead_click': '⚫ HOLT KATTINTÁS (gather helyett)',
            'new_troops': 'Új egység gomb',
            'march_button': 'March gomb',
            'screen_center': 'Képernyő közepe'
        }
        
        # Meglévő koordináták betöltése
        coords_file = self.config_dir / 'farm_coords.json'
        if coords_file.exists():
            try:
                with open(coords_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        all_coords = json.loads(content)
                    else:
                        all_coords = {}
                print("ℹ️  Meglévő koordináták betöltve.\n")
            except json.JSONDecodeError:
                print("⚠️ Hibás JSON, új koordináták létrehozása...\n")
                all_coords = {}
        else:
            all_coords = {}
        
        # Csak azokhoz a farmokhoz kérjük a koordinátákat, amikhez van régió
        active_farms = [name for name, region in farm_regions.items() if region is not None]
        
        for farm_type in active_farms:
            print(f"\n{'='*60}")
            print(f"🌾 {farm_type.upper()} FARM KOORDINÁTÁK")
            print(f"{'='*60}")
            
            # Meglévő koordináták a farm típushoz
            coords = all_coords.get(farm_type)
            if coords is None or not isinstance(coords, dict):
                coords = {}
            
            for coord_name in coord_names:
                label = coord_labels[coord_name]
                
                # Holt kattintás jelzése
                if coord_name == 'dead_click':
                    print(f"\n⚫ {label}")
                    print(f"   ⚠️  NEM MENTŐDIK - csak a setup folytonosságához")
                    print(f"   Kattints bárhova a folytatáshoz...")
                else:
                    old_coord = coords.get(coord_name)
                    
                    if old_coord:
                        print(f"\n📍 {label} - Jelenlegi: {old_coord}")
                    else:
                        print(f"\n📍 {label} - Nincs beállítva")
                    
                    print(f"   Kattints a játékban, vagy ESC = régi megtartása")
                
                coord = self.get_single_coordinate()
                
                # Holt kattintást NEM mentjük
                if coord_name == 'dead_click':
                    if coord:
                        print(f"   ✅ Holt kattintás OK (nem mentve)")
                    else:
                        print(f"   ⏹️  ESC - Kihagyva")
                    continue  # ← NEM menti el!
                
                # Többi koordináta normálisan
                if coord and coord != [0, 0]:
                    coords[coord_name] = coord
                    print(f"   ✅ {label} frissítve: {coord}")
                else:
                    if old_coord:
                        print(f"   ℹ️  {label} régi érték megtartva")
                    else:
                        coords[coord_name] = [0, 0]
                        print(f"   ⚠️ {label} default: [0, 0]")
            
            all_coords[farm_type] = coords
        
        # Mentés
        with open(coords_file, 'w', encoding='utf-8') as f:
            json.dump(all_coords, f, indent=2)
        
        print(f"\n✅ Farm koordináták mentve: {coords_file}")
        return all_coords
    
    def get_single_coordinate(self):
        """Egyetlen koordináta bekérése kattintással"""
        coord = [None]
        cancelled = [False]
        done = [False]
        
        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                coord[0] = [x, y]
                done[0] = True
                print(f"   🖱️ Koordináta: ({x}, {y})")
                return False
        
        def on_press(key):
            try:
                if key == keyboard.Key.esc:
                    print(f"   ⏹️  ESC - Kihagyva")
                    cancelled[0] = True
                    done[0] = True
                    return False
            except:
                pass
        
        # Listeners indítása
        mouse_listener = mouse.Listener(on_click=on_click)
        keyboard_listener = keyboard.Listener(on_press=on_press)
        
        mouse_listener.start()
        keyboard_listener.start()
        
        # Várakozás bármelyik befejezésére
        import time
        while not done[0]:
            time.sleep(0.1)
        
        # Listeners leállítása
        mouse_listener.stop()
        keyboard_listener.stop()
        
        # Ha ESC volt, None-t ad vissza
        if cancelled[0]:
            return None
        
        return coord[0] if coord[0] else [0, 0]
    
    def setup_gather_template(self):
        """Gather.png template mentése"""
        print("\nGather gomb template mentése!")
        print("⚠️  FONTOS: A gather gomb RANDOM helyen lehet!")
        print("Ezért NEM koordinátát, hanem KÉPET mentünk róla.\n")
        
        gather_path = self.images_dir / 'gather.png'
        
        if gather_path.exists():
            print(f"ℹ️  Meglévő gather.png: {gather_path}")
        else:
            print("Nincs meglévő gather.png\n")
        
        # Vár ENTER-re vagy ESC-re
        if not self.wait_for_enter_or_esc("ENTER = új képernyőkép"):
            if gather_path.exists():
                print(f"  ℹ️  Gather template megtartva")
            else:
                print("  ⚠️ Gather template kihagyva")
            return
        
        region = self.selector.select_region("GATHER GOMB")
        
        if region:
            # Screenshot és kivágás
            screen = ImageGrab.grab()
            screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            cropped = screen_np[y:y+h, x:x+w]
            
            # Mentés
            cv2.imwrite(str(gather_path), cropped)
            
            print(f"\n✅ Gather template mentve: {gather_path}")
            print(f"   Méret: {w}x{h} pixel")
            print(f"   ⚠️  Template matching fogja használni (0.7 threshold)")
        else:
            if gather_path.exists():
                print(f"  ℹ️  Gather template megtartva")
            else:
                print("  ⚠️ Gather template kihagyva")
    
    def setup_explorer_coordinates(self):
        """Explorer koordináták és régiók beállítása"""
        print("\nExplorer koordináták beállítása kattintással!")
        print("\n📋 EXPLORER FOLYAMAT:")
        print("  1. Que menü megnyitása")
        print("  2. Que fül bezárása")
        print("  3. Scout fül megnyitása")
        print("  4-5. Felfedezés % régiók (2 db)")
        print("  6. Scout bezárása")
        print("  7. Que fül megnyitása")
        print("  8. Que menü bezárása")
        print("\n📋 EXPLORATION INDÍTÁS:")
        print("  9. Scout épület")
        print("  10. Explore gomb")
        print("\nESC = kihagyás (régi érték megtartása)\n")

        coord_names = [
            'open_queue_menu',      # 1. Que menü megnyitása
            'close_queue_tab',      # 2. Que fül bezárása
            'open_scout_tab',       # 3. Scout fül megnyitása
            'exploration_region_1', # 4. Felfedezés % régió 1 (RÉGIÓ!)
            'exploration_region_2', # 5. Felfedezés % régió 2 (RÉGIÓ!)
            'close_scout',          # 6. Scout bezárása
            'open_queue_tab',       # 7. Que fül megnyitása
            'close_queue_menu',     # 8. Que menü bezárása
            'scout_building',       # 9. Scout épület
            'explore_button'        # 10. Explore gomb
        ]

        coord_labels = {
            'open_queue_menu': 'Que menü megnyitása',
            'close_queue_tab': 'Que fül bezárása',
            'open_scout_tab': 'Scout fül megnyitása',
            'exploration_region_1': '📦 Felfedezés % régió 1 (TERÜLET!)',
            'exploration_region_2': '📦 Felfedezés % régió 2 (TERÜLET!)',
            'close_scout': 'Scout bezárása',
            'open_queue_tab': 'Que fül megnyitása',
            'close_queue_menu': 'Que menü bezárása',
            'scout_building': 'Scout épület',
            'explore_button': 'Explore gomb'
        }

        # Meglévő koordináták betöltése
        coords_file = self.config_dir / 'explorer_coords.json'
        if coords_file.exists():
            try:
                with open(coords_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        coords = json.loads(content)
                    else:
                        coords = {}
                print("ℹ️  Meglévő explorer koordináták betöltve.\n")
            except json.JSONDecodeError:
                print("⚠️ Hibás JSON, új koordináták létrehozása...\n")
                coords = {}
        else:
            coords = {}

        for coord_name in coord_names:
            label = coord_labels[coord_name]
            old_coord = coords.get(coord_name)

            # Régiók esetén más kezelés
            if 'region' in coord_name:
                if old_coord:
                    print(f"\n📦 {label} - Jelenlegi: (x:{old_coord['x']}, y:{old_coord['y']}, w:{old_coord['width']}, h:{old_coord['height']})")
                else:
                    print(f"\n📦 {label} - Nincs beállítva")

                print(f"   Jelöld ki a területet, vagy ESC = régi megtartása")

                if not self.wait_for_enter_or_esc("ENTER = új terület"):
                    if old_coord:
                        print(f"   ℹ️  {label} régi érték megtartva")
                    else:
                        coords[coord_name] = None
                        print(f"   ⚠️ {label} kihagyva")
                    continue

                region = self.selector.select_region(label)

                if region:
                    coords[coord_name] = region
                    print(f"   ✅ {label} frissítve: (x:{region['x']}, y:{region['y']}, w:{region['width']}, h:{region['height']})")
                else:
                    if old_coord:
                        print(f"   ℹ️  {label} régi érték megtartva")
                    else:
                        coords[coord_name] = None
                        print(f"   ⚠️ {label} kihagyva")
            else:
                # Koordináták esetén
                if old_coord:
                    print(f"\n📍 {label} - Jelenlegi: {old_coord}")
                else:
                    print(f"\n📍 {label} - Nincs beállítva")

                print(f"   Kattints a játékban, vagy ESC = régi megtartása")

                coord = self.get_single_coordinate()

                if coord and coord != [0, 0]:
                    coords[coord_name] = coord
                    print(f"   ✅ {label} frissítve: {coord}")
                else:
                    if old_coord:
                        print(f"   ℹ️  {label} régi érték megtartva")
                    else:
                        coords[coord_name] = [0, 0]
                        print(f"   ⚠️ {label} default: [0, 0]")

        # Mentés
        with open(coords_file, 'w', encoding='utf-8') as f:
            json.dump(coords, f, indent=2)

        print(f"\n✅ Explorer koordináták mentve: {coords_file}")
        return coords

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
            "default_march_time": 60,
            "default_gather_time": 5400
        }
        
        settings_file = self.config_dir / 'settings.json'
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        
        print("\n✅ Alapértelmezett beállítások:")
        print(f"   Repeat count: {settings['repeat_count']}")
        print(f"   Max cycles: {settings['max_cycles']}")
        print(f"   Human wait: {settings['human_wait_min']}-{settings['human_wait_max']} sec")
        print(f"   Gather retry: {settings['gather_retry_attempts']}x")
        
        print(f"\n💾 Mentve: {settings_file}")


def main():
    """Main entry point"""
    
    # Játék ablak ellenőrzése
    if not initialize_game_window("BlueStacks"):
        print("\n⚠️ Játék ablak nem található!")
        print("Indítsd el a játékot, majd futtasd újra a setup-ot.\n")
        return
    
    wizard = SetupWizard()
    wizard.run()


if __name__ == "__main__":
    main()