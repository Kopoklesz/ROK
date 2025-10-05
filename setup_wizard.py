"""
ROK Auto Farm - Setup Wizard (Menu-Based v2.0)
Teljes menürendszer minden beállításhoz
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
            print("0. Vissza")
            print("\n" + "="*60)
            
            choice = self.get_menu_choice(0, 4)
            
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
    
    def setup_resource_regions(self):
        """Resource OCR régiók beállítása"""
        print("\n" + "="*60)
        print("📍 RESOURCE REGIONS SETUP")
        print("="*60)
        print("\nJelöld ki az erőforrás számokat a képernyőn!")
        print("ESC = skip (megtartja a régi értéket)")
        
        resources = ['wheat', 'wood', 'stone', 'gold']
        
        # Meglévő régiók betöltése
        regions_file = self.config_dir / 'farm_regions.json'
        if regions_file.exists():
            with open(regions_file, 'r', encoding='utf-8') as f:
                regions = json.load(f)
        else:
            regions = {}
        
        for resource in resources:
            old_value = regions.get(resource)
            if old_value:
                print(f"\n📍 {resource.upper()} - Jelenlegi: {old_value}")
            else:
                print(f"\n📍 {resource.upper()} - Nincs beállítva")
            
            if not self.wait_for_enter_or_esc("ENTER = új régió"):
                if old_value:
                    print(f"  ℹ️  {resource.upper()} megtartva")
                else:
                    regions[resource] = None
                continue
            
            region = self.selector.select_region(f"{resource.upper()} számláló")
            
            if region:
                regions[resource] = region
                print(f"  ✅ {resource.upper()} frissítve")
            else:
                if old_value:
                    print(f"  ℹ️  {resource.upper()} megtartva")
                else:
                    regions[resource] = None
        
        # Mentés
        with open(regions_file, 'w', encoding='utf-8') as f:
            json.dump(regions, f, indent=2)
        
        print(f"\n✅ Resource régiók mentve: {regions_file}")
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    def setup_time_regions(self):
        """Time OCR régiók beállítása"""
        print("\n" + "="*60)
        print("📍 TIME REGIONS SETUP")
        print("="*60)
        print("\nJelöld ki az idő területeket!")
        
        # Meglévő régiók betöltése
        time_file = self.config_dir / 'time_regions.json'
        if time_file.exists():
            with open(time_file, 'r', encoding='utf-8') as f:
                time_regions = json.load(f)
        else:
            time_regions = {}
        
        # March Time
        old_value = time_regions.get('march_time')
        if old_value:
            print(f"\n📍 MARCH TIME - Jelenlegi: {old_value}")
        else:
            print(f"\n📍 MARCH TIME - Nincs beállítva")
        
        if self.wait_for_enter_or_esc("ENTER = új régió"):
            region = self.selector.select_region("MARCH TIME")
            if region:
                time_regions['march_time'] = region
                print(f"  ✅ March Time frissítve")
        
        # Gather Time
        old_value = time_regions.get('gather_time')
        if old_value:
            print(f"\n📍 GATHER TIME - Jelenlegi: {old_value}")
        else:
            print(f"\n📍 GATHER TIME - Nincs beállítva")
        
        if self.wait_for_enter_or_esc("ENTER = új régió"):
            region = self.selector.select_region("GATHER TIME")
            if region:
                time_regions['gather_time'] = region
                print(f"  ✅ Gather Time frissítve")
        
        # Mentés
        with open(time_file, 'w', encoding='utf-8') as f:
            json.dump(time_regions, f, indent=2)
        
        print(f"\n✅ Time régiók mentve: {time_file}")
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    def setup_farm_coordinates(self):
        """Farm koordináták beállítása"""
        print("\n" + "="*60)
        print("📍 FARM COORDINATES SETUP")
        print("="*60)
        print("\n📋 KOORDINÁTA SORREND:")
        print("  1. Resource icon (nyersanyag ikon)")
        print("  2. Level button (szint)")
        print("  3. Search button (keresés)")
        print("  4. ⚫ HOLT KATTINTÁS (gather helyett - NEM mentődik!)")
        print("  5. New troops (új egység)")
        print("  6. March button (march)")
        print("  7. Screen center (képernyő közepe)")
        print("\nESC = skip")
        
        coord_names = [
            'resource_icon', 'level_button', 'search_button',
            'dead_click', 'new_troops', 'march_button', 'screen_center'
        ]
        
        coord_labels = {
            'resource_icon': 'Resource icon',
            'level_button': 'Level button',
            'search_button': 'Search button',
            'dead_click': '⚫ HOLT KATTINTÁS',
            'new_troops': 'New troops',
            'march_button': 'March button',
            'screen_center': 'Screen center'
        }
        
        # Meglévő koordináták betöltése
        coords_file = self.config_dir / 'farm_coords.json'
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                all_coords = json.load(f)
        else:
            all_coords = {}
        
        # Farm regions betöltése (melyik farm enabled)
        regions_file = self.config_dir / 'farm_regions.json'
        if regions_file.exists():
            with open(regions_file, 'r', encoding='utf-8') as f:
                farm_regions = json.load(f)
        else:
            farm_regions = {}
        
        active_farms = [name for name, region in farm_regions.items() if region is not None]
        
        if not active_farms:
            print("\n⚠️ Nincs enabled farm! Először állítsd be a Resource Regions-t!")
            input("\nNyomj ENTER-t a folytatáshoz...")
            return
        
        for farm_type in active_farms:
            print(f"\n{'='*60}")
            print(f"🌾 {farm_type.upper()} FARM KOORDINÁTÁK")
            print(f"{'='*60}")
            
            coords = all_coords.get(farm_type, {})
            
            for coord_name in coord_names:
                label = coord_labels[coord_name]
                
                if coord_name == 'dead_click':
                    print(f"\n⚫ {label}")
                    print(f"   ⚠️  NEM MENTŐDIK - folytonosság miatt")
                    print(f"   Kattints bárhova...")
                    coord = self.get_single_coordinate()
                    if coord:
                        print(f"   ✅ OK (nem mentve)")
                    continue
                
                old_coord = coords.get(coord_name)
                if old_coord:
                    print(f"\n📍 {label} - Jelenlegi: {old_coord}")
                else:
                    print(f"\n📍 {label} - Nincs beállítva")
                
                print(f"   Kattints a játékban, vagy ESC = skip")
                
                coord = self.get_single_coordinate()
                
                if coord and coord != [0, 0]:
                    coords[coord_name] = coord
                    print(f"   ✅ {label} frissítve")
                else:
                    if old_coord:
                        print(f"   ℹ️  {label} megtartva")
                    else:
                        coords[coord_name] = [0, 0]
            
            all_coords[farm_type] = coords
        
        # Mentés
        with open(coords_file, 'w', encoding='utf-8') as f:
            json.dump(all_coords, f, indent=2)
        
        print(f"\n✅ Farm koordináták mentve: {coords_file}")
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    def setup_gather_template(self):
        """Gather.png template mentése"""
        print("\n" + "="*60)
        print("📍 GATHER TEMPLATE SETUP")
        print("="*60)
        
        gather_path = self.images_dir / 'gather.png'
        
        if gather_path.exists():
            print(f"\nℹ️  Meglévő: {gather_path}")
        
        if not self.wait_for_enter_or_esc("ENTER = új template"):
            print("  ℹ️  Template megtartva")
            return
        
        region = self.selector.select_region("GATHER GOMB")
        
        if region:
            screen = ImageGrab.grab()
            screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            cropped = screen_np[y:y+h, x:x+w]
            
            cv2.imwrite(str(gather_path), cropped)
            
            print(f"\n✅ Gather template mentve: {gather_path}")
            print(f"   Méret: {w}x{h} pixel")
        else:
            print("  ⚠️  Template kihagyva")
        
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    # ===== TRAINING MENU =====
    
    def training_menu(self):
        """Training setup almenü"""
        while True:
            print("\n" + "="*60)
            print("⚔️  TRAINING SETUP")
            print("="*60)
            print("\n1. Training Time Regions (barracks, archery, stable, siege)")
            print("2. Training Coordinates (building icons, max, train)")
            print("0. Vissza")
            print("\n" + "="*60)
            
            choice = self.get_menu_choice(0, 2)
            
            if choice == 0:
                break
            elif choice == 1:
                self.setup_training_time_regions()
            elif choice == 2:
                self.setup_training_coordinates()
    
    def setup_training_time_regions(self):
        """Training time OCR régiók"""
        print("\n" + "="*60)
        print("📍 TRAINING TIME REGIONS SETUP")
        print("="*60)
        
        buildings = ['barracks', 'archery', 'stable', 'siege']
        
        # Meglévő régiók betöltése
        time_file = self.config_dir / 'training_time_regions.json'
        if time_file.exists():
            with open(time_file, 'r', encoding='utf-8') as f:
                time_regions = json.load(f)
        else:
            time_regions = {}
        
        for building in buildings:
            region_key = f"{building}_time"
            old_value = time_regions.get(region_key)
            
            if old_value:
                print(f"\n📍 {building.upper()} TIME - Jelenlegi: {old_value}")
            else:
                print(f"\n📍 {building.upper()} TIME - Nincs beállítva")
            
            if not self.wait_for_enter_or_esc("ENTER = új régió"):
                continue
            
            region = self.selector.select_region(f"{building.upper()} TIME")
            
            if region:
                time_regions[region_key] = region
                print(f"  ✅ {building.upper()} time frissítve")
        
        # Mentés
        with open(time_file, 'w', encoding='utf-8') as f:
            json.dump(time_regions, f, indent=2)
        
        print(f"\n✅ Training time régiók mentve: {time_file}")
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    def setup_training_coordinates(self):
        """Training koordináták"""
        print("\n" + "="*60)
        print("📍 TRAINING COORDINATES SETUP")
        print("="*60)
        
        buildings = ['barracks', 'archery', 'stable', 'siege']
        coord_names = ['building_icon', 'max_button', 'train_button']
        
        # Meglévő koordináták betöltése
        coords_file = self.config_dir / 'training_coords.json'
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                all_coords = json.load(f)
        else:
            all_coords = {}
        
        for building in buildings:
            print(f"\n{'='*60}")
            print(f"⚔️  {building.upper()} KOORDINÁTÁK")
            print(f"{'='*60}")
            
            coords = all_coords.get(building, {})
            
            for coord_name in coord_names:
                old_coord = coords.get(coord_name)
                
                if old_coord:
                    print(f"\n📍 {coord_name} - Jelenlegi: {old_coord}")
                else:
                    print(f"\n📍 {coord_name} - Nincs beállítva")
                
                print(f"   Kattints, vagy ESC = skip")
                coord = self.get_single_coordinate()
                
                if coord and coord != [0, 0]:
                    coords[coord_name] = coord
                    print(f"   ✅ {coord_name} frissítve")
            
            all_coords[building] = coords
        
        # Mentés
        with open(coords_file, 'w', encoding='utf-8') as f:
            json.dump(all_coords, f, indent=2)
        
        print(f"\n✅ Training koordináták mentve: {coords_file}")
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    # ===== ALLIANCE MENU =====
    
    def alliance_menu(self):
        """Alliance setup almenü"""
        while True:
            print("\n" + "="*60)
            print("🤝 ALLIANCE SETUP")
            print("="*60)
            print("\n1. hand.png Template")
            print("2. hand.png Locations (2 koordináta)")
            print("0. Vissza")
            print("\n" + "="*60)
            
            choice = self.get_menu_choice(0, 2)
            
            if choice == 0:
                break
            elif choice == 1:
                self.setup_hand_template()
            elif choice == 2:
                self.setup_hand_locations()
    
    def setup_hand_template(self):
        """hand.png template"""
        print("\n" + "="*60)
        print("📍 HAND TEMPLATE SETUP")
        print("="*60)
        
        hand_path = self.images_dir / 'hand.png'
        
        if hand_path.exists():
            print(f"\nℹ️  Meglévő: {hand_path}")
        
        if not self.wait_for_enter_or_esc("ENTER = új template"):
            return
        
        region = self.selector.select_region("HAND ICON")
        
        if region:
            screen = ImageGrab.grab()
            screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            cropped = screen_np[y:y+h, x:x+w]
            
            cv2.imwrite(str(hand_path), cropped)
            print(f"\n✅ Hand template mentve: {hand_path}")
        
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    def setup_hand_locations(self):
        """hand.png locations (2 koordináta)"""
        print("\n" + "="*60)
        print("📍 HAND LOCATIONS SETUP")
        print("="*60)
        print("\nKattints 2 helyre ahol a hand ikon megjelenhet!")
        
        # Meglévő betöltése
        coords_file = self.config_dir / 'alliance_coords.json'
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                alliance_coords = json.load(f)
        else:
            alliance_coords = {'hand_locations': [{'x': 0, 'y': 0}, {'x': 0, 'y': 0}]}
        
        locations = alliance_coords.get('hand_locations', [])
        
        for i in range(2):
            old_loc = locations[i] if i < len(locations) else {'x': 0, 'y': 0}
            print(f"\n📍 Location #{i+1} - Jelenlegi: {old_loc}")
            print("   Kattints, vagy ESC = skip")
            
            coord = self.get_single_coordinate()
            
            if coord:
                if i < len(locations):
                    locations[i] = {'x': coord[0], 'y': coord[1]}
                else:
                    locations.append({'x': coord[0], 'y': coord[1]})
                print(f"   ✅ Location #{i+1} frissítve")
        
        alliance_coords['hand_locations'] = locations
        
        # Mentés
        with open(coords_file, 'w', encoding='utf-8') as f:
            json.dump(alliance_coords, f, indent=2)
        
        print(f"\n✅ Hand locations mentve: {coords_file}")
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    # ===== ANTI-AFK MENU =====
    
    def anti_afk_menu(self):
        """Anti-AFK setup almenü"""
        while True:
            print("\n" + "="*60)
            print("🔄 ANTI-AFK SETUP")
            print("="*60)
            print("\n1. resource1.png Template")
            print("2. resource2.png Template")
            print("3. resource3.png Template")
            print("4. resource4.png Template")
            print("0. Vissza")
            print("\n" + "="*60)
            
            choice = self.get_menu_choice(0, 4)
            
            if choice == 0:
                break
            elif 1 <= choice <= 4:
                self.setup_resource_template(choice)
    
    def setup_resource_template(self, resource_num):
        """Resource template (1-4)"""
        print(f"\n📍 resource{resource_num}.png TEMPLATE SETUP")
        
        resource_path = self.images_dir / f'resource{resource_num}.png'
        
        if resource_path.exists():
            print(f"ℹ️  Meglévő: {resource_path}")
        
        if not self.wait_for_enter_or_esc("ENTER = új template"):
            return
        
        region = self.selector.select_region(f"RESOURCE {resource_num}")
        
        if region:
            screen = ImageGrab.grab()
            screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            cropped = screen_np[y:y+h, x:x+w]
            
            cv2.imwrite(str(resource_path), cropped)
            print(f"\n✅ resource{resource_num}.png mentve: {resource_path}")
        
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    # ===== SETTINGS MENU =====
    
    def settings_menu(self):
        """Settings almenü"""
        while True:
            print("\n" + "="*60)
            print("⚙️  SETTINGS")
            print("="*60)
            print("\n1. Commander Count")
            print("2. Timer Intervals")
            print("3. Human Wait Times")
            print("0. Vissza")
            print("\n" + "="*60)
            
            choice = self.get_menu_choice(0, 3)
            
            if choice == 0:
                break
            elif choice == 1:
                self.setup_commander_count()
            elif choice == 2:
                self.setup_timer_intervals()
            elif choice == 3:
                self.setup_human_wait()
    
    def setup_commander_count(self):
        """Commander count beállítás"""
        print("\n📍 COMMANDER COUNT SETUP")
        
        try:
            count = int(input("Hány commander-t használsz? (1-5): "))
            
            if not (1 <= count <= 5):
                print("⚠️  Hibás érték (1-5)")
                return
            
            # Settings frissítés
            settings_file = self.config_dir / 'settings.json'
            
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = self.create_default_settings()
            
            if 'gathering' not in settings:
                settings['gathering'] = {}
            
            settings['gathering']['max_commanders'] = count
            settings['gathering']['commanders'] = [
                {"id": i+1, "enabled": True} for i in range(count)
            ]
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            print(f"✅ Commander count: {count}")
        
        except ValueError:
            print("⚠️  Számot adj meg!")
        
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    def setup_timer_intervals(self):
        """Timer intervals"""
        print("\n📍 TIMER INTERVALS SETUP")
        
        settings_file = self.config_dir / 'settings.json'
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            settings = self.create_default_settings()
        
        try:
            print("\nAlliance check interval (sec):")
            print(f"  Jelenlegi: {settings.get('alliance', {}).get('check_interval_seconds', 1800)}")
            alliance_int = int(input("  Új érték (1800 = 30 perc): "))
            
            print("\nAnti-AFK idle threshold (sec):")
            print(f"  Jelenlegi: {settings.get('anti_afk', {}).get('idle_threshold_seconds', 900)}")
            afk_threshold = int(input("  Új érték (900 = 15 perc): "))
            
            if 'alliance' not in settings:
                settings['alliance'] = {}
            settings['alliance']['check_interval_seconds'] = alliance_int
            
            if 'anti_afk' not in settings:
                settings['anti_afk'] = {}
            settings['anti_afk']['idle_threshold_seconds'] = afk_threshold
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            print("\n✅ Timer intervals frissítve")
        
        except ValueError:
            print("⚠️  Számot adj meg!")
        
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    def setup_human_wait(self):
        """Human wait times"""
        print("\n📍 HUMAN WAIT TIMES SETUP")
        
        settings_file = self.config_dir / 'settings.json'
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            settings = self.create_default_settings()
        
        try:
            print("\nHuman wait minimum (sec):")
            print(f"  Jelenlegi: {settings.get('human_wait', {}).get('min_seconds', 5)}")
            min_sec = int(input("  Új érték: "))
            
            print("\nHuman wait maximum (sec):")
            print(f"  Jelenlegi: {settings.get('human_wait', {}).get('max_seconds', 10)}")
            max_sec = int(input("  Új érték: "))
            
            if 'human_wait' not in settings:
                settings['human_wait'] = {}
            settings['human_wait']['min_seconds'] = min_sec
            settings['human_wait']['max_seconds'] = max_sec
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            print("\n✅ Human wait times frissítve")
        
        except ValueError:
            print("⚠️  Számot adj meg!")
        
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    # ===== TEST MENU =====
    
    def test_menu(self):
        """Test & Verify almenü"""
        print("\n" + "="*60)
        print("✅ TEST & VERIFY")
        print("="*60)
        print("\n⚠️  TODO: OCR Test, Image Matching Test, Coordinate Test")
        print("Később implementáljuk!")
        input("\nNyomj ENTER-t a folytatáshoz...")
    
    # ===== HELPER METHODS =====
    
    def get_menu_choice(self, min_val, max_val):
        """Menü választás bekérése"""
        while True:
            try:
                choice = int(input(f"\nVálasztás ({min_val}-{max_val}): "))
                if min_val <= choice <= max_val:
                    return choice
                else:
                    print(f"⚠️  Hibás választás! ({min_val}-{max_val})")
            except ValueError:
                print("⚠️  Számot adj meg!")
            except KeyboardInterrupt:
                print("\n\n⚠️  Setup megszakítva")
                return 0
    
    def wait_for_enter_or_esc(self, prompt="ENTER = folytatás"):
        """Vár ENTER-re vagy ESC-re"""
        print(f"  {prompt}, ESC = skip")
        
        cancelled = [False]
        
        def on_press(key):
            try:
                if key == keyboard.Key.enter:
                    return False
                elif key == keyboard.Key.esc:
                    cancelled[0] = True
                    print(f"  ⏹️  ESC - Skip")
                    return False
            except:
                pass
        
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        listener.join()
        
        return not cancelled[0]
    
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
                    print(f"   ⏹️  ESC - Skip")
                    cancelled[0] = True
                    done[0] = True
                    return False
            except:
                pass
        
        mouse_listener = mouse.Listener(on_click=on_click)
        keyboard_listener = keyboard.Listener(on_press=on_press)
        
        mouse_listener.start()
        keyboard_listener.start()
        
        import time
        while not done[0]:
            time.sleep(0.1)
        
        mouse_listener.stop()
        keyboard_listener.stop()
        
        if cancelled[0]:
            return None
        
        return coord[0] if coord[0] else [0, 0]
    
    def create_default_settings(self):
        """Alapértelmezett settings létrehozása"""
        return {
            "gathering": {
                "max_commanders": 4,
                "commanders": [
                    {"id": 1, "enabled": True},
                    {"id": 2, "enabled": True},
                    {"id": 3, "enabled": True},
                    {"id": 4, "enabled": True}
                ]
            },
            "training": {
                "buildings": {
                    "barracks": {"enabled": True, "troop_type": "tier1_infantry", "prep_time_seconds": 300},
                    "archery": {"enabled": False},
                    "stable": {"enabled": True, "troop_type": "tier1_cavalry", "prep_time_seconds": 300},
                    "siege": {"enabled": False}
                }
            },
            "alliance": {"enabled": True, "check_interval_seconds": 1800},
            "anti_afk": {"enabled": True, "idle_threshold_seconds": 900, "resource_offset_y": 50},
            "human_wait": {"min_seconds": 5, "max_seconds": 10},
            "startup_wait": {"min_seconds": 20, "max_seconds": 25},
            "defaults": {"march_time_seconds": 300, "gather_time_seconds": 5400}
        }


def main():
    """Main entry point"""
    
    # Játék ablak ellenőrzése
    if not initialize_game_window("BlueStacks"):
        print("\n⚠️ Játék ablak nem található!")
        print("Indítsd el a játékot, majd futtasd újra a setup-ot.\n")
        return
    
    wizard = SetupWizardMenu()
    wizard.run()


if __name__ == "__main__":
    main()