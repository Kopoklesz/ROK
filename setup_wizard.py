"""
ROK Auto Farm - Setup Wizard (Menu-Based v2.0 COMPLETE)
FIXED: Minden hiányzó függvény implementálva
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
    """Setup wizard menürendszerrel - TELJES IMPLEMENTÁCIÓ"""

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
            choice = self.get_menu_choice(0, 9)

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
                self.connection_lost_menu()
            elif choice == 6:
                self.explorer_menu()
            elif choice == 7:
                self.settings_menu()
            elif choice == 8:
                self.test_menu()
            elif choice == 9:
                self.advanced_tools_menu()

    def show_main_menu(self):
        """Főmenü megjelenítése"""
        print("\n" + "="*60)
        print("ROK AUTO FARM - SETUP WIZARD v2.1 ML-ENHANCED")
        print("="*60)
        print("\n1. 🌾 Gathering Setup")
        print("2. ⚔️  Training Setup")
        print("3. 🤝 Alliance Setup")
        print("4. 🔄 Anti-AFK Setup")
        print("5. 🔌 Connection Lost Setup")
        print("6. 🔍 Explorer Setup")
        print("7. ⚙️  Settings")
        print("8. ✅ Test & Verify")
        print("9. 🔧 Advanced Tools (ML/Template)")
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
            print("5. March.png Template")
            print("6. March Detection Region")
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

    def setup_resource_regions(self):
        """Resource OCR régiók beállítása (wheat, wood, stone, gold)"""
        print("\n" + "="*60)
        print("📍 RESOURCE REGIONS SETUP")
        print("="*60)
        print("\nJelöld ki az erőforrás számokat (OCR régiók)")
        print("4 erőforrás: wheat, wood, stone, gold")
        print("\n⚠️  FONTOS: Csak a számokat jelöld ki, semmi mást!")

        # Config betöltés
        regions_file = self.config_dir / 'farm_regions.json'
        if regions_file.exists():
            with open(regions_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}

        resources = ['wheat', 'wood', 'stone', 'gold']

        for resource in resources:
            print("\n" + "-"*60)
            print(f"🌾 {resource.upper()}")
            print("-"*60)

            # Meglévő érték
            old_value = config.get(resource)
            if old_value:
                print(f"ℹ️  Jelenlegi: {old_value}")
            else:
                print(f"ℹ️  Nincs beállítva")

            if not self.wait_for_enter_or_esc(f"ENTER = {resource} régió kijelölése, ESC = skip"):
                continue

            region = self.selector.select_region(f"{resource.upper()} NUMBER (csak a szám!)")

            if region:
                config[resource] = region
                print(f"✅ {resource} régió mentve: x={region['x']}, y={region['y']}, w={region['width']}, h={region['height']}")

        # Mentés
        with open(regions_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        print("\n" + "="*60)
        print(f"✅ Resource regions mentve: {regions_file}")
        print("="*60)
        input("\nNyomj ENTER-t a folytatáshoz...")

    def setup_time_regions(self):
        """Time OCR régiók beállítása (march_time, gather_time)"""
        print("\n" + "="*60)
        print("📍 TIME REGIONS SETUP")
        print("="*60)
        print("\nJelöld ki az idő régiókat (OCR)")
        print("2 idő: march_time, gather_time")

        # Config betöltés
        time_file = self.config_dir / 'time_regions.json'
        if time_file.exists():
            with open(time_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}

        times = [
            ('march_time', 'March Time (menet idő)'),
            ('gather_time', 'Gather Time (gyűjtés idő)')
        ]

        for time_key, time_desc in times:
            print("\n" + "-"*60)
            print(f"⏱️  {time_desc}")
            print("-"*60)

            # Meglévő érték
            old_value = config.get(time_key)
            if old_value:
                print(f"ℹ️  Jelenlegi: {old_value}")
            else:
                print(f"ℹ️  Nincs beállítva")

            print("\n⚠️  KRITIKUS: CSAK az időt jelöld ki, NE a teljes sort!")
            print("⚠️  Példa: '5m 30s' vagy '1h 20m' - CSAK ez a szöveg, semmi más!")
            print("⚠️  gather_time esetén különösen fontos a pontos kijelölés!")

            if not self.wait_for_enter_or_esc(f"ENTER = {time_key} régió, ESC = skip"):
                continue

            region = self.selector.select_region(f"{time_desc.upper()} (CSAK AZ IDŐ!)")

            if region:
                config[time_key] = region
                print(f"✅ {time_key} mentve: x={region['x']}, y={region['y']}, w={region['width']}, h={region['height']}")

        # Mentés
        with open(time_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        print("\n" + "="*60)
        print(f"✅ Time regions mentve: {time_file}")
        print("="*60)
        input("\nNyomj ENTER-t a folytatáshoz...")

    def setup_farm_coordinates(self):
        """Farm koordináták beállítása"""
        print("\n" + "="*60)
        print("📍 FARM COORDINATES SETUP")
        print("="*60)
        print("\nJelöld ki a farm koordinátákat (kattintási pontok)")
        print("4 farm típus: wheat, wood, stone, gold")
        print("\nMinden farm típushoz 6 koordináta szükséges:")
        print("  1. resource_icon - Erőforrás ikon a térképen")
        print("  2. level_button - Szint gomb")
        print("  3. search_button - Keresés gomb")
        print("  4. new_troops - Új csapatok gomb")
        print("  5. march_button - March/Indulás gomb")
        print("  6. screen_center - Képernyő közepe")

        # Config betöltés
        coords_file = self.config_dir / 'farm_coords.json'
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}

        resources = ['wheat', 'wood', 'stone', 'gold']

        coord_types = [
            ('resource_icon', 'Resource Icon (erőforrás gomb)'),
            ('level_button', 'Level Button (szint gomb)'),
            ('search_button', 'Search Button (keresés gomb)'),
            ('new_troops', 'New Troops (új csapatok)'),
            ('march_button', 'March Button (indulás gomb)'),
            ('screen_center', 'Screen Center (képernyő közepe)')
        ]

        for resource in resources:
            print("\n" + "="*60)
            print(f"🌾 {resource.upper()} FARM")
            print("="*60)

            if resource not in config:
                config[resource] = {}

            for coord_key, coord_desc in coord_types:
                print("\n" + "-"*60)
                print(f"📍 {coord_desc}")
                print("-"*60)

                # Meglévő érték
                old_value = config[resource].get(coord_key)
                if old_value:
                    print(f"ℹ️  Jelenlegi: {old_value}")
                else:
                    print(f"ℹ️  Nincs beállítva")

                if not self.wait_for_enter_or_esc(f"ENTER = {coord_key} kijelölése, ESC = skip"):
                    continue

                # Koordináta kijelölés (régió középpontja lesz a koordináta)
                print("\nJelöld ki a gombot/területet (a középpontja lesz a kattintási pont)")
                region = self.selector.select_region(f"{resource.upper()} - {coord_desc}")

                if region:
                    # Régió középpontja = koordináta
                    x = region['x'] + region['width'] // 2
                    y = region['y'] + region['height'] // 2
                    config[resource][coord_key] = [x, y]
                    print(f"✅ {coord_key} mentve: ({x}, {y})")

        # Mentés
        with open(coords_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        print("\n" + "="*60)
        print(f"✅ Farm coordinates mentve: {coords_file}")
        print("="*60)
        input("\nNyomj ENTER-t a folytatáshoz...")

    def setup_gather_template(self):
        """Gather.png template mentése"""
        print("\n" + "="*60)
        print("📍 GATHER.PNG TEMPLATE SETUP")
        print("="*60)
        print("\nJelöld ki a 'Gather' gombot!")
        print("Ezt a template-et használja a bot gather gomb kereséséhez.")

        gather_path = self.images_dir / 'gather.png'

        if gather_path.exists():
            print(f"\nℹ️  Meglévő: {gather_path}")

        if not self.wait_for_enter_or_esc("ENTER = új template, ESC = skip"):
            return

        region = self.selector.select_region("GATHER BUTTON")

        if region:
            screen = ImageGrab.grab()
            screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            cropped = screen_np[y:y+h, x:x+w]

            cv2.imwrite(str(gather_path), cropped)
            print(f"\n✅ Gather template mentve: {gather_path}")

        input("\nNyomj ENTER-t a folytatáshoz...")

    def setup_march_template(self):
        """March.png template (commander már úton detektáláshoz)"""
        print("\n" + "="*60)
        print("📍 MARCH.PNG TEMPLATE SETUP")
        print("="*60)
        print("\nJelöld ki a 'march' szöveget vagy ikont!")
        print("(Ezt keresi a bot, hogy ellenőrizze van-e már commander úton)")

        march_path = self.images_dir / 'march.png'

        if march_path.exists():
            print(f"\nℹ️  Meglévő: {march_path}")

        if not self.wait_for_enter_or_esc("ENTER = új template, ESC = skip"):
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
        """March detekciós régió (hol keresse a march template-et)"""
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

        if not self.wait_for_enter_or_esc("ENTER = új régió, ESC = skip"):
            return

        region = self.selector.select_region("MARCH DETECTION REGION")

        if region:
            config['march_detection_region'] = region

            with open(gathering_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            print(f"\n✅ March detection region mentve")

        input("\nNyomj ENTER-t a folytatáshoz...")

    # ===== TRAINING MENU =====

    def training_menu(self):
        """Training setup almenü"""
        while True:
            print("\n" + "="*60)
            print("⚔️  TRAINING SETUP")
            print("="*60)
            print("\n1. Training Time Regions (barracks, archery, stable, siege)")
            print("2. Training Coordinates (kattintási pontok)")
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
        """Training time OCR régiók (barracks_time, archery_time, stb.)"""
        print("\n" + "="*60)
        print("📍 TRAINING TIME REGIONS SETUP")
        print("="*60)
        print("\nJelöld ki a training time régiókat (OCR)")
        print("\n⚠️  FONTOS: Csak az időt jelöld ki!")

        # Config betöltés
        time_file = self.config_dir / 'training_time_regions.json'
        if time_file.exists():
            with open(time_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}

        # ===== UPGRADE DETECTION REGIONS =====
        print("\n" + "="*60)
        print("🔧 UPGRADE DETECTION RÉGIÓK")
        print("="*60)
        print("\nElőször a fejlesztés detektáláshoz szükséges régiók:")
        print("  - upgrade_name_region_1: Első régió ahol épület neve megjelenhet")
        print("  - upgrade_name_region_2: Második régió ahol épület neve megjelenhet")

        upgrade_name_regions = [
            ('upgrade_name_region_1', 'Upgrade Name Region 1 (épület név 1. helye)'),
            ('upgrade_name_region_2', 'Upgrade Name Region 2 (épület név 2. helye)')
        ]

        for region_key, region_desc in upgrade_name_regions:
            print("\n" + "-"*60)
            print(f"🔧 {region_desc}")
            print("-"*60)

            # Meglévő érték
            old_value = config.get(region_key)
            if old_value:
                print(f"ℹ️  Jelenlegi: {old_value}")
            else:
                print(f"ℹ️  Nincs beállítva")

            if not self.wait_for_enter_or_esc(f"ENTER = {region_key} régió, ESC = skip"):
                continue

            region = self.selector.select_region(f"{region_desc.upper()}")

            if region:
                config[region_key] = region
                print(f"✅ {region_key} mentve: x={region['x']}, y={region['y']}, w={region['width']}, h={region['height']}")

        # ===== UPGRADE TIME REGIONS =====
        print("\n" + "="*60)
        print("⏱️  UPGRADE TIME RÉGIÓK")
        print("="*60)
        print("\nAz upgrade time 2 közös régióban jelenik meg:")
        print("  - upgrade_time_region_1: Első hely ahol upgrade time megjelenhet")
        print("  - upgrade_time_region_2: Második hely ahol upgrade time megjelenhet")

        upgrade_time_regions = [
            ('upgrade_time_region_1', 'Upgrade Time Region 1 (upgrade idő 1. helye)'),
            ('upgrade_time_region_2', 'Upgrade Time Region 2 (upgrade idő 2. helye)')
        ]

        for region_key, region_desc in upgrade_time_regions:
            print("\n" + "-"*60)
            print(f"⏱️  {region_desc}")
            print("-"*60)

            # Meglévő érték
            old_value = config.get(region_key)
            if old_value:
                print(f"ℹ️  Jelenlegi: {old_value}")
            else:
                print(f"ℹ️  Nincs beállítva")

            if not self.wait_for_enter_or_esc(f"ENTER = {region_key} régió, ESC = skip"):
                continue

            region = self.selector.select_region(f"{region_desc.upper()}")

            if region:
                config[region_key] = region
                print(f"✅ {region_key} mentve: x={region['x']}, y={region['y']}, w={region['width']}, h={region['height']}")

        # ===== TRAINING TIME REGIONS =====
        print("\n" + "="*60)
        print("⏱️  TRAINING TIME RÉGIÓK (4 épület)")
        print("="*60)
        print("\n4 épület: barracks, archery, stable, siege")

        buildings = [
            ('barracks_time', 'Barracks Time (laktanya idő)'),
            ('archery_time', 'Archery Time (íjász idő)'),
            ('stable_time', 'Stable Time (istálló idő)'),
            ('siege_time', 'Siege Time (ostrom idő)')
        ]

        for time_key, time_desc in buildings:
            print("\n" + "-"*60)
            print(f"⏱️  {time_desc}")
            print("-"*60)

            # Meglévő érték
            old_value = config.get(time_key)
            if old_value:
                print(f"ℹ️  Jelenlegi: {old_value}")
            else:
                print(f"ℹ️  Nincs beállítva")

            if not self.wait_for_enter_or_esc(f"ENTER = {time_key} régió, ESC = skip"):
                continue

            region = self.selector.select_region(f"{time_desc.upper()} (CSAK AZ IDŐ!)")

            if region:
                config[time_key] = region
                print(f"✅ {time_key} mentve: x={region['x']}, y={region['y']}, w={region['width']}, h={region['height']}")

        # Mentés
        with open(time_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        print("\n" + "="*60)
        print(f"✅ Training time regions mentve: {time_file}")
        print("="*60)
        input("\nNyomj ENTER-t a folytatáshoz...")

    def setup_training_coordinates(self):
        """Training koordináták (panel + épületek)"""
        print("\n" + "="*60)
        print("📍 TRAINING COORDINATES SETUP")
        print("="*60)
        print("\nJelöld ki a training koordinátákat (pontos kattintással)")
        print("\n⚠️  FONTOS: Csak KATTINTS a gomb közepére, nem kell tartományt húzni!")

        # Config betöltés
        coords_file = self.config_dir / 'training_coords.json'
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}

        # ===== PANEL KOORDINÁTÁK =====
        print("\n" + "="*60)
        print("🔲 PANEL KOORDINÁTÁK")
        print("="*60)
        print("\nElőször a training panel megnyitás/bezárás gombjai:")

        panel_coords = [
            ('open_panel', 'Panel megnyitás gomb'),
            ('close_panel', 'Panel bezárás gomb'),
            ('upgrade_check_button', 'Upgrade check gomb (opcionális, ha van ilyen)')
        ]

        for coord_key, coord_desc in panel_coords:
            print("\n" + "-"*60)
            print(f"📍 {coord_desc}")
            print("-"*60)

            # Meglévő érték
            old_value = config.get(coord_key)
            if old_value:
                print(f"ℹ️  Jelenlegi: {old_value}")
            else:
                print(f"ℹ️  Nincs beállítva")

            if not self.wait_for_enter_or_esc(f"ENTER = {coord_key}, ESC = skip"):
                continue

            # Pont kijelölés
            point = self.selector.select_point(coord_desc)

            if point:
                config[coord_key] = point
                print(f"✅ {coord_key} mentve: ({point[0]}, {point[1]})")

        # ===== ÉPÜLET KOORDINÁTÁK =====
        print("\n" + "="*60)
        print("🏰 ÉPÜLET KOORDINÁTÁK")
        print("="*60)
        print("\n4 épület: barracks, archery, stable, siege")
        print("\nMinden épülethez 5 koordináta szükséges:")
        print("  1. troop_gather - Csapat gyűjtés gomb")
        print("  2. building - Épület gomb")
        print("  3. button - Akció gomb")
        print("  4. tier - Tier kiválasztás")
        print("  5. confirm - Megerősítés gomb")

        buildings = ['barracks', 'archery', 'stable', 'siege']

        coord_types = [
            ('troop_gather', 'Troop Gather (csapat gyűjtés)'),
            ('building', 'Building (épület)'),
            ('button', 'Button (gomb)'),
            ('tier', 'Tier (szint)'),
            ('confirm', 'Confirm (megerősítés)')
        ]

        for building in buildings:
            print("\n" + "="*60)
            print(f"⚔️  {building.upper()}")
            print("="*60)

            if building not in config:
                config[building] = {}

            for coord_key, coord_desc in coord_types:
                print("\n" + "-"*60)
                print(f"📍 {coord_desc}")
                print("-"*60)

                # Meglévő érték
                old_value = config[building].get(coord_key)
                if old_value:
                    print(f"ℹ️  Jelenlegi: {old_value}")
                else:
                    print(f"ℹ️  Nincs beállítva")

                if not self.wait_for_enter_or_esc(f"ENTER = {coord_key}, ESC = skip"):
                    continue

                # Pont kijelölés (nem tartomány!)
                point = self.selector.select_point(f"{building.upper()} - {coord_desc}")

                if point:
                    config[building][coord_key] = point
                    print(f"✅ {coord_key} mentve: ({point[0]}, {point[1]})")

        # Mentés
        with open(coords_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        print("\n" + "="*60)
        print(f"✅ Training coordinates mentve: {coords_file}")
        print("="*60)
        input("\nNyomj ENTER-t a folytatáshoz...")

    # ===== ALLIANCE MENU =====

    def alliance_menu(self):
        """Alliance setup almenü"""
        while True:
            print("\n" + "="*60)
            print("🤝 ALLIANCE SETUP")
            print("="*60)
            print("\n1. Hand Locations (2 koordináta)")
            print("2. hand.png Template")
            print("0. Vissza")
            print("\n" + "="*60)

            choice = self.get_menu_choice(0, 2)

            if choice == 0:
                break
            elif choice == 1:
                self.setup_hand_locations()
            elif choice == 2:
                self.setup_hand_template()

    def setup_hand_locations(self):
        """Hand locations (fix koordináták)"""
        print("\n" + "="*60)
        print("📍 HAND LOCATIONS SETUP")
        print("="*60)
        print("\nJelöld ki a hand gomb lehetséges pozícióit (max 2 db)")
        print("Ezek fix koordináták, ahova a bot kattintani fog.")

        # Config betöltés
        coords_file = self.config_dir / 'alliance_coords.json'
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}

        # Meglévő értékek
        old_value = config.get('hand_locations', [])
        if old_value:
            print(f"\nℹ️  Jelenlegi: {len(old_value)} db koordináta")
            for idx, loc in enumerate(old_value, 1):
                print(f"    #{idx}: ({loc['x']}, {loc['y']})")
        else:
            print(f"\nℹ️  Nincs beállítva")

        if not self.wait_for_enter_or_esc("ENTER = új koordináták, ESC = skip"):
            return

        locations = []

        for i in range(2):
            print(f"\n--- Location #{i+1} ---")

            if not self.wait_for_enter_or_esc(f"ENTER = location #{i+1} kijelölése, ESC = skip"):
                break

            region = self.selector.select_region(f"HAND LOCATION #{i+1}")

            if region:
                x = region['x'] + region['width'] // 2
                y = region['y'] + region['height'] // 2
                locations.append({'x': x, 'y': y})
                print(f"✅ Location #{i+1} mentve: ({x}, {y})")

        if locations:
            config['hand_locations'] = locations

            with open(coords_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            print(f"\n✅ {len(locations)} db hand location mentve")

        input("\nNyomj ENTER-t a folytatáshoz...")

    def setup_hand_template(self):
        """hand.png template mentése"""
        print("\n" + "="*60)
        print("📍 HAND.PNG TEMPLATE SETUP")
        print("="*60)
        print("\nJelöld ki a 'hand' ikont!")
        print("Ez fallback, ha a fix koordináták nem működnek.")

        hand_path = self.images_dir / 'hand.png'

        if hand_path.exists():
            print(f"\nℹ️  Meglévő: {hand_path}")

        if not self.wait_for_enter_or_esc("ENTER = új template, ESC = skip"):
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

    # ===== ANTI-AFK MENU =====

    def anti_afk_menu(self):
        """Anti-AFK setup almenü"""
        while True:
            print("\n" + "="*60)
            print("🔄 ANTI-AFK SETUP")
            print("="*60)
            print("\n1. Resource Templates (resource1-4.png)")
            print("0. Vissza")
            print("\n" + "="*60)

            choice = self.get_menu_choice(0, 1)

            if choice == 0:
                break
            elif choice == 1:
                self.setup_resource_templates()

    def setup_resource_templates(self):
        """Resource templates (resource1-4.png)"""
        print("\n" + "="*60)
        print("📍 RESOURCE TEMPLATES SETUP")
        print("="*60)
        print("\nJelöld ki a resource ikonokat (max 4 db)")
        print("Ezek az AFK detekció resource collection-höz kellenek.")

        for i in range(1, 5):
            print(f"\n--- Resource #{i} ---")

            resource_path = self.images_dir / f'resource{i}.png'

            if resource_path.exists():
                print(f"ℹ️  Meglévő: {resource_path}")

            if not self.wait_for_enter_or_esc(f"ENTER = resource{i}.png, ESC = skip"):
                continue

            region = self.selector.select_region(f"RESOURCE ICON #{i}")

            if region:
                screen = ImageGrab.grab()
                screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

                x, y, w, h = region['x'], region['y'], region['width'], region['height']
                cropped = screen_np[y:y+h, x:x+w]

                cv2.imwrite(str(resource_path), cropped)
                print(f"✅ resource{i}.png mentve")

        input("\nNyomj ENTER-t a folytatáshoz...")

    # ===== CONNECTION LOST MENU =====

    def connection_lost_menu(self):
        """Connection Lost setup almenü"""
        while True:
            print("\n" + "="*60)
            print("🔌 CONNECTION LOST SETUP")
            print("="*60)
            print("\n1. Detection Region (OCR terület)")
            print("2. Confirm Button Coordinate")
            print("3. Enable/Disable")
            print("4. Advanced Settings")
            print("0. Vissza")
            print("\n" + "="*60)

            choice = self.get_menu_choice(0, 4)

            if choice == 0:
                break
            elif choice == 1:
                self.setup_connection_detection_region()
            elif choice == 2:
                self.setup_connection_confirm_button()
            elif choice == 3:
                self.setup_connection_enable()
            elif choice == 4:
                self.setup_connection_advanced()

    def setup_connection_detection_region(self):
        """Connection Lost detection region beállítása"""
        print("\n" + "="*60)
        print("📍 NETWORK DISCONNECTED DETECTION REGION")
        print("="*60)
        print("\nJelöld ki azt a területet, ahol a 'NETWORK DISCONNECTED' szöveg megjelenhet!")
        print("(Például az ablak közepén, ahol az üzenet látható)")

        # Config betöltés
        config_file = self.config_dir / 'connection_monitor.json'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {
                "enabled": False,
                "check_interval_seconds": 5,
                "detection_region": None,
                "detection_text": "NETWORK DISCONNECTED",
                "confirm_button": None,
                "recovery_wait_seconds": 30,
                "default_recovery_time_seconds": 5400
            }

        # Meglévő érték
        old_value = config.get('detection_region')
        if old_value:
            print(f"\nℹ️  Jelenlegi: {old_value}")
        else:
            print(f"\nℹ️  Nincs beállítva")

        if not self.wait_for_enter_or_esc("ENTER = detection region kijelölése, ESC = skip"):
            return

        region = self.selector.select_region("NETWORK DISCONNECTED TEXT REGION")

        if region:
            config['detection_region'] = region

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            print(f"\n✅ Detection region mentve")

        input("\nNyomj ENTER-t a folytatáshoz...")

    def setup_connection_confirm_button(self):
        """Connection Lost confirm button beállítása"""
        print("\n" + "="*60)
        print("📍 CONNECTION LOST CONFIRM BUTTON")
        print("="*60)
        print("\nKattints a 'Confirm' vagy 'OK' gomb közepére!")
        print("\n⚠️  FONTOS: Csak KATTINTS a gomb közepére, nem kell tartományt húzni!")

        # Config betöltés
        config_file = self.config_dir / 'connection_monitor.json'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {
                "enabled": False,
                "check_interval_seconds": 5,
                "detection_region": None,
                "detection_text": "NETWORK DISCONNECTED",
                "confirm_button": None,
                "recovery_wait_seconds": 30,
                "default_recovery_time_seconds": 5400
            }

        # Meglévő érték
        old_value = config.get('confirm_button')
        if old_value:
            print(f"\nℹ️  Jelenlegi: {old_value}")
        else:
            print(f"\nℹ️  Nincs beállítva")

        if not self.wait_for_enter_or_esc("ENTER = confirm button kijelölése, ESC = skip"):
            return

        # Pont kijelölés
        point = self.selector.select_point("CONFIRM BUTTON")

        if point:
            config['confirm_button'] = point

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            print(f"\n✅ Confirm button mentve: ({point[0]}, {point[1]})")

        input("\nNyomj ENTER-t a folytatáshoz...")

    def setup_connection_enable(self):
        """Connection Lost enable/disable"""
        print("\n" + "="*60)
        print("⚙️  CONNECTION LOST ENABLE/DISABLE")
        print("="*60)

        # Config betöltés
        config_file = self.config_dir / 'connection_monitor.json'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {
                "enabled": False,
                "check_interval_seconds": 5,
                "detection_region": None,
                "detection_text": "NETWORK DISCONNECTED",
                "confirm_button": None,
                "recovery_wait_seconds": 30,
                "default_recovery_time_seconds": 5400
            }

        current = config.get('enabled', False)
        print(f"\nℹ️  Jelenlegi állapot: {'ENABLED ✅' if current else 'DISABLED ❌'}")

        print("\n1. Enable")
        print("2. Disable")
        print("0. Vissza")

        choice = self.get_menu_choice(0, 2)

        if choice == 1:
            config['enabled'] = True
            print("\n✅ Connection Lost monitor ENABLED")
        elif choice == 2:
            config['enabled'] = False
            print("\n❌ Connection Lost monitor DISABLED")
        else:
            return

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        input("\nNyomj ENTER-t a folytatáshoz...")

    def setup_connection_advanced(self):
        """Connection Lost advanced settings"""
        print("\n" + "="*60)
        print("⚙️  CONNECTION LOST ADVANCED SETTINGS")
        print("="*60)
        print("\nℹ️  Szerkeszd manuálisan: config/connection_monitor.json")
        print("\nBeállítható paraméterek:")
        print("  - check_interval_seconds: Ellenőrzési gyakoriság (default: 5)")
        print("  - detection_text: Keresett szöveg (default: 'NETWORK DISCONNECTED')")
        print("  - recovery_wait_seconds: Várakozás confirm után (default: 30)")
        print("  - default_recovery_time_seconds: Default recovery idő (default: 5400 = 1.5 óra)")
        input("\nNyomj ENTER-t a folytatáshoz...")

    # ===== EXPLORER MENU =====

    def explorer_menu(self):
        """Explorer menü"""
        print("\n" + "="*60)
        print("🔍 EXPLORER SETUP")
        print("="*60)
        print("\n1. Setup Explorer Coordinates")
        print("0. Back")
        print("\n" + "="*60)

        choice = self.get_menu_choice(0, 1)

        if choice == 1:
            self.setup_explorer_coordinates()

    def setup_explorer_coordinates(self):
        """Explorer koordináták és régiók beállítása"""
        print("\n" + "="*60)
        print("📍 EXPLORER COORDINATES SETUP")
        print("="*60)
        print("\nExplorer koordináták beállítása kattintással!")
        print("\n📋 EXPLORER FOLYAMAT:")
        print("  1. Que menü megnyitása")
        print("  2. Que fül bezárása")
        print("  3. Scout fül megnyitása")
        print("  4-6. Felfedezés % régiók (3 db)")
        print("  7. Scout bezárása")
        print("  8. Que fül megnyitása")
        print("  9. Que menü bezárása")
        print("\n📋 EXPLORATION INDÍTÁS:")
        print("  10. Scout épület")
        print("  11. Pre-explore gomb (új!)")
        print("  12. Explore gomb")
        print("\n⚠️  ENTER = új koordináta beállítása, ESC = régi megtartása\n")

        coord_names = [
            'open_queue_menu',      # 1. Que menü megnyitása
            'close_queue_tab',      # 2. Que fül bezárása
            'open_scout_tab',       # 3. Scout fül megnyitása
            'exploration_region_1', # 4. Felfedezés % régió 1 (RÉGIÓ!)
            'exploration_region_2', # 5. Felfedezés % régió 2 (RÉGIÓ!)
            'exploration_region_3', # 6. Felfedezés % régió 3 (RÉGIÓ!) - ÚJ!
            'close_scout',          # 7. Scout bezárása
            'open_queue_tab',       # 8. Que fül megnyitása
            'close_queue_menu',     # 9. Que menü bezárása
            'scout_building',       # 10. Scout épület
            'pre_explore_button',   # 11. Pre-explore gomb - ÚJ!
            'explore_button'        # 12. Explore gomb
        ]

        coord_labels = {
            'open_queue_menu': 'Que menü megnyitása',
            'close_queue_tab': 'Que fül bezárása',
            'open_scout_tab': 'Scout fül megnyitása',
            'exploration_region_1': '📦 Felfedezés % régió 1 (TERÜLET!)',
            'exploration_region_2': '📦 Felfedezés % régió 2 (TERÜLET!)',
            'exploration_region_3': '📦 Felfedezés % régió 3 (TERÜLET!)',
            'close_scout': 'Scout bezárása',
            'open_queue_tab': 'Que fül megnyitása',
            'close_queue_menu': 'Que menü bezárása',
            'scout_building': 'Scout épület',
            'pre_explore_button': 'Pre-explore gomb (explore előtt)',
            'explore_button': 'Explore gomb (végleges)'
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
                print("\n" + "-"*60)
                print(f"📍 {label}")
                print("-"*60)

                if old_coord:
                    print(f"ℹ️  Jelenlegi: {old_coord}")
                else:
                    print(f"ℹ️  Nincs beállítva")

                # ENTER/ESC kérdés (mint a training/gathering-nál)
                if not self.wait_for_enter_or_esc(f"ENTER = {coord_name} beállítása, ESC = skip"):
                    if old_coord:
                        print(f"ℹ️  Régi érték megtartva")
                    continue

                print(f"\n   🖱️  Kattints a gomb közepére a játékban...")
                coord = self.get_single_coordinate()

                if coord and coord != [0, 0]:
                    coords[coord_name] = coord
                    print(f"✅ {coord_name} mentve: {coord}")
                else:
                    if old_coord:
                        print(f"ℹ️  Régi érték megtartva")
                    else:
                        coords[coord_name] = [0, 0]
                        print(f"⚠️  Kihagyva, default: [0, 0]")

        # Mentés
        with open(coords_file, 'w', encoding='utf-8') as f:
            json.dump(coords, f, indent=2)

        print(f"\n" + "="*60)
        print(f"✅ Explorer koordináták mentve: {coords_file}")
        print("="*60)
        input("\nNyomj ENTER-t a folytatáshoz...")

    # ===== SETTINGS MENU =====

    def settings_menu(self):
        """Settings.json szerkesztő"""
        print("\n" + "="*60)
        print("⚙️  SETTINGS")
        print("="*60)
        print("\nℹ️  Szerkeszd manuálisan: config/settings.json")
        print("\nJelenleg a következő beállítások módosíthatóak:")
        print("  - gathering.commanders (enabled/disabled)")
        print("  - training.buildings (enabled/disabled)")
        print("  - alliance.enabled")
        print("  - anti_afk.enabled")
        print("  - human_wait (min_seconds, max_seconds)")
        print("\nTODO: Interaktív settings szerkesztő implementálása")
        input("\nNyomj ENTER-t a folytatáshoz...")

    # ===== TEST MENU =====

    def test_menu(self):
        """Test & Verify menü - IMPLEMENTÁLVA"""
        while True:
            print("\n" + "="*60)
            print("✅ TEST & VERIFY")
            print("="*60)
            print("\n1. Validate All Configs")
            print("2. Visualize Coordinates (Screenshot)")
            print("3. Visualize OCR Regions (Screenshot)")
            print("4. Test OCR Regions (Live)")
            print("5. Run Full Test Suite")
            print("6. Test Module (Training/Gathering/Explorer)")
            print("0. Vissza")
            print("\n" + "="*60)

            choice = self.get_menu_choice(0, 6)

            if choice == 0:
                break
            elif choice == 1:
                self.validate_configs()
            elif choice == 2:
                self.visualize_coordinates()
            elif choice == 3:
                self.visualize_ocr_regions()
            elif choice == 4:
                self.test_ocr_live()
            elif choice == 5:
                self.run_full_test()
            elif choice == 6:
                self.test_module()

    def validate_configs(self):
        """Config validálás futtatása"""
        print("\n" + "="*60)
        print("CONFIG VALIDÁLÁS")
        print("="*60)

        import subprocess
        result = subprocess.run([
            'python3',
            'tools/config_validator.py',
            '--mode', 'check'
        ], cwd=Path(__file__).parent)

        input("\nNyomj ENTER-t a folytatáshoz...")

    def visualize_coordinates(self):
        """Koordináták vizualizálása"""
        print("\n" + "="*60)
        print("KOORDINÁTA VIZUALIZÁCIÓ")
        print("="*60)
        print("\nVálaszd ki a típust:")
        print("1. Training koordináták")
        print("2. Gathering koordináták")
        print("3. Alliance koordináták")
        print("4. Összes koordináta")
        print("0. Vissza")

        choice = self.get_menu_choice(0, 4)

        if choice == 0:
            return

        type_map = {
            1: 'training',
            2: 'gathering',
            3: 'alliance',
            4: 'all'
        }

        import subprocess
        result = subprocess.run([
            'python3',
            'tools/config_validator.py',
            '--mode', 'visual-coords',
            '--type', type_map[choice]
        ], cwd=Path(__file__).parent)

        print("\n✅ Vizualizáció kész! Nézd meg: logs/config_visualization.png")
        input("\nNyomj ENTER-t a folytatáshoz...")

    def visualize_ocr_regions(self):
        """OCR régiók vizualizálása"""
        print("\n" + "="*60)
        print("OCR RÉGIÓ VIZUALIZÁCIÓ")
        print("="*60)
        print("\nVálaszd ki a típust:")
        print("1. Training régiók")
        print("2. Resource régiók")
        print("3. Gathering régiók")
        print("4. Összes régió")
        print("0. Vissza")

        choice = self.get_menu_choice(0, 4)

        if choice == 0:
            return

        type_map = {
            1: 'training',
            2: 'resource',
            3: 'gathering',
            4: 'all'
        }

        import subprocess
        result = subprocess.run([
            'python3',
            'tools/config_validator.py',
            '--mode', 'visual-ocr',
            '--type', type_map[choice]
        ], cwd=Path(__file__).parent)

        print("\n✅ Vizualizáció kész! Nézd meg: logs/ocr_regions_visualization.png")
        input("\nNyomj ENTER-t a folytatáshoz...")

    def test_ocr_live(self):
        """OCR régiók élő tesztelése"""
        print("\n" + "="*60)
        print("OCR RÉGIÓ ÉLŐBEN TESZT")
        print("="*60)
        print("\nMost az összes OCR régiót tesztelni fogom élőben.")
        print("Győződj meg róla hogy a játék látszik!")

        input("\nNyomj ENTER-t ha készen állsz...")

        import subprocess
        result = subprocess.run([
            'python3',
            'tools/config_validator.py',
            '--mode', 'test-ocr'
        ], cwd=Path(__file__).parent)

        input("\nNyomj ENTER-t a folytatáshoz...")

    def run_full_test(self):
        """Teljes teszt suite futtatása"""
        print("\n" + "="*60)
        print("TELJES TESZT SUITE")
        print("="*60)
        print("\nMinden teszt fut:")
        print("  1. Config validálás")
        print("  2. Koordináta vizualizáció")
        print("  3. OCR régió vizualizáció")
        print("  4. OCR élő teszt")

        input("\nNyomj ENTER-t az indításhoz...")

        import subprocess
        result = subprocess.run([
            'python3',
            'tools/config_validator.py',
            '--mode', 'all'
        ], cwd=Path(__file__).parent)

        print("\n✅ Teljes teszt kész!")
        print("Nézd meg az eredményeket:")
        print("  - logs/config_visualization.png")
        print("  - logs/ocr_regions_visualization.png")
        input("\nNyomj ENTER-t a folytatáshoz...")

    def test_module(self):
        """Module tesztelés vizualizációval"""
        print("\n" + "="*60)
        print("MODULE TESZTELÉS")
        print("="*60)
        print("\nVálaszd ki a modult:")
        print("1. Training Manager")
        print("2. Gathering Manager")
        print("3. Explorer Manager")
        print("0. Vissza")

        choice = self.get_menu_choice(0, 3)

        if choice == 0:
            return

        module_map = {
            1: 'training',
            2: 'gathering',
            3: 'explorer'
        }

        module_name = module_map[choice]

        print(f"\n🧪 {module_name.upper()} teszt indul...")
        print("\nMit fog csinálni:")
        print("  - Lépésről-lépésre végigmegy a modul folyamatán")
        print("  - Minden lépésnél screenshot-ot készít")
        print("  - Vizualizálja a kattintásokat/OCR-eket")
        print("  - HTML riportot generál")
        print(f"\nEredmények: logs/module_tests/{module_name}/")

        input("\nNyomj ENTER-t az indításhoz...")

        import subprocess
        result = subprocess.run([
            'python3',
            'tools/module_tester.py',
            '--module', module_name
        ], cwd=Path(__file__).parent)

        print(f"\n✅ {module_name.upper()} teszt kész!")
        print(f"\nNézd meg a riportot:")
        print(f"  - logs/module_tests/{module_name}/*_report.html")
        print(f"  - logs/module_tests/{module_name}/*.png (screenshot-ok)")
        input("\nNyomj ENTER-t a folytatáshoz...")

    # ===== ADVANCED TOOLS MENU =====

    def advanced_tools_menu(self):
        """Advanced tools - ML/Template matching"""
        while True:
            print("\n" + "="*60)
            print("🔧 ADVANCED TOOLS")
            print("="*60)
            print("\n1. Capture Button Template (koordinátából)")
            print("2. Test Template Matching")
            print("3. Test EasyOCR vs Tesseract")
            print("4. Batch Template Capture (több gomb)")
            print("0. Vissza")
            print("\n" + "="*60)

            choice = self.get_menu_choice(0, 4)

            if choice == 0:
                break
            elif choice == 1:
                self.capture_button_template()
            elif choice == 2:
                self.test_template_matching()
            elif choice == 3:
                self.test_ocr_comparison()
            elif choice == 4:
                self.batch_template_capture()

    def capture_button_template(self):
        """Button template capture koordinátából"""
        from library import ImageManager

        print("\n" + "="*60)
        print("📸 BUTTON TEMPLATE CAPTURE")
        print("="*60)
        print("\nEz a funkció egy gomb koordinátájából készít template-et.")
        print("Használat: Ha van egy koordinátád, de template-et szeretnél belőle.\n")

        # Template neve
        template_name = input("Template neve (pl: training_button): ").strip()
        if not template_name:
            print("❌ Név megadása kötelező!")
            input("\nNyomj ENTER-t a folytatáshoz...")
            return

        # Koordináta bekérése
        print("\nVálaszd ki a módot:")
        print("1. Kattintással megadás")
        print("2. Manuális koordináta beírás")
        print("0. Mégse")

        mode = self.get_menu_choice(0, 2)
        if mode == 0:
            return

        coord = None
        if mode == 1:
            print("\n🖱️  Kattints a gomb közepére...")
            coord = self.get_single_coordinate()
        else:
            try:
                x = int(input("X koordináta: "))
                y = int(input("Y koordináta: "))
                coord = [x, y]
            except ValueError:
                print("❌ Érvénytelen koordináta!")
                input("\nNyomj ENTER-t a folytatáshoz...")
                return

        if not coord or coord == [0, 0]:
            print("❌ Érvénytelen koordináta!")
            input("\nNyomj ENTER-t a folytatáshoz...")
            return

        # Template méret
        print(f"\nTemplate méret? (default: 80x80)")
        width_str = input("Szélesség (vagy ENTER = 80): ").strip()
        height_str = input("Magasság (vagy ENTER = 80): ").strip()

        width = int(width_str) if width_str else 80
        height = int(height_str) if height_str else 80

        # Capture
        output_path = self.images_dir / f"{template_name}.png"

        print(f"\n📸 Template capture: {coord} ({width}x{height})")
        template = ImageManager.capture_button_template(
            coord[0], coord[1],
            width=width,
            height=height,
            output_path=str(output_path)
        )

        if template is not None:
            print(f"✅ Template mentve: {output_path}")
        else:
            print("❌ Template capture sikertelen!")

        input("\nNyomj ENTER-t a folytatáshoz...")

    def test_template_matching(self):
        """Template matching teszt"""
        from library import ImageManager

        print("\n" + "="*60)
        print("🔍 TEMPLATE MATCHING TESZT")
        print("="*60)
        print("\nElérhető template-ek:")

        # Template lista
        templates = list(self.images_dir.glob("*.png"))
        if not templates:
            print("❌ Nincs template az images/ mappában!")
            input("\nNyomj ENTER-t a folytatáshoz...")
            return

        for i, tpl in enumerate(templates, 1):
            print(f"  {i}. {tpl.name}")

        print("\n0. Vissza")

        choice = self.get_menu_choice(0, len(templates))
        if choice == 0:
            return

        template_path = str(templates[choice - 1])

        # Threshold beállítás
        print(f"\nEgyezési küszöb? (0.0-1.0, default: 0.7)")
        threshold_str = input("Threshold (vagy ENTER = 0.7): ").strip()
        threshold = float(threshold_str) if threshold_str else 0.7

        # Multi-scale?
        print("\nMulti-scale matching? (lassabb, de robusztusabb)")
        print("1. Igen (több méret próbálása)")
        print("2. Nem (csak 1:1)")
        multi_scale = self.get_menu_choice(1, 2) == 1

        # Test
        print(f"\n🔍 Template keresése: {templates[choice - 1].name}")
        print(f"   Threshold: {threshold}, Multi-scale: {multi_scale}")

        coords = ImageManager.find_image(template_path, threshold=threshold, multi_scale=multi_scale)

        if coords:
            print(f"✅ Template megtalálva: {coords}")
        else:
            print("❌ Template nem található!")

        input("\nNyomj ENTER-t a folytatáshoz...")

    def test_ocr_comparison(self):
        """EasyOCR vs Tesseract összehasonlítás"""
        from library import ImageManager

        print("\n" + "="*60)
        print("🤖 OCR ÖSSZEHASONLÍTÁS")
        print("="*60)
        print("\nEz a teszt összehasonlítja az EasyOCR és Tesseract eredményeit.")
        print("Válassz egy OCR régiót a teszteléshez.\n")

        # Config listázás
        print("Válassz config-ot:")
        print("1. Training time régiók")
        print("2. Resource régiók")
        print("0. Vissza")

        choice = self.get_menu_choice(0, 2)
        if choice == 0:
            return

        # Config betöltése
        if choice == 1:
            config_file = self.config_dir / 'training_time_regions.json'
        else:
            config_file = self.config_dir / 'resource_regions.json'

        if not config_file.exists():
            print(f"❌ Config nem található: {config_file}")
            input("\nNyomj ENTER-t a folytatáshoz...")
            return

        with open(config_file, 'r', encoding='utf-8') as f:
            regions = json.load(f)

        # Régió választás
        region_list = list(regions.keys())
        print("\nVálaszd ki a régiót:")
        for i, region_name in enumerate(region_list, 1):
            print(f"  {i}. {region_name}")
        print("0. Vissza")

        region_choice = self.get_menu_choice(0, len(region_list))
        if region_choice == 0:
            return

        region_name = region_list[region_choice - 1]
        region = regions[region_name]

        # OCR teszt - EasyOCR
        print(f"\n🤖 EasyOCR teszt: {region_name}")
        text_easyocr = ImageManager.read_text_from_region(region, use_easyocr=True, debug_save=True)
        print(f"   Eredmény: '{text_easyocr}'")

        # OCR teszt - Tesseract only
        print(f"\n📝 Tesseract teszt: {region_name}")
        text_tesseract = ImageManager.read_text_from_region(region, use_easyocr=False, debug_save=True)
        print(f"   Eredmény: '{text_tesseract}'")

        # Összehasonlítás
        print("\n" + "="*60)
        print("EREDMÉNYEK")
        print("="*60)
        print(f"EasyOCR:    '{text_easyocr}'")
        print(f"Tesseract:  '{text_tesseract}'")

        if text_easyocr == text_tesseract:
            print("\n✅ Azonos eredmény!")
        else:
            print("\n⚠️  Eltérő eredmény!")

        input("\nNyomj ENTER-t a folytatáshoz...")

    def batch_template_capture(self):
        """Több gomb template capture egyszerre"""
        from library import ImageManager

        print("\n" + "="*60)
        print("📸 BATCH TEMPLATE CAPTURE")
        print("="*60)
        print("\nEz a funkció több gombot egyszerre kap el template-ként.")
        print("Például: training panel mind a 4 building gombja.\n")

        # Config választás
        print("Válassz config-ot:")
        print("1. Training coords (buildings)")
        print("2. Gathering coords (map, search)")
        print("3. Alliance coords (alliance, help)")
        print("0. Vissza")

        choice = self.get_menu_choice(0, 3)
        if choice == 0:
            return

        # Config betöltése
        config_map = {
            1: ('training_coords.json', ['barracks.button', 'archery.button', 'stable.button', 'siege.button']),
            2: ('gathering_coords.json', ['map_button', 'search_button']),
            3: ('alliance_coords.json', ['alliance_button', 'help_button'])
        }

        config_file, coord_keys = config_map[choice]
        config_path = self.config_dir / config_file

        if not config_path.exists():
            print(f"❌ Config nem található: {config_path}")
            input("\nNyomj ENTER-t a folytatáshoz...")
            return

        with open(config_path, 'r', encoding='utf-8') as f:
            coords = json.load(f)

        # Template capture
        print(f"\n📸 Template capture: {len(coord_keys)} gomb")

        for key in coord_keys:
            # Koordináta lekérése
            if '.' in key:
                # Nested (pl: barracks.button)
                parts = key.split('.')
                coord = coords.get(parts[0], {}).get(parts[1])
                template_name = f"{parts[0]}_{parts[1]}"
            else:
                # Flat (pl: map_button)
                coord = coords.get(key)
                template_name = key

            if not coord or coord == [0, 0]:
                print(f"⚠️  {key}: nincs beállítva, skip")
                continue

            # Capture
            output_path = self.images_dir / f"{template_name}.png"
            print(f"\n   📸 {template_name}: {coord}")

            template = ImageManager.capture_button_template(
                coord[0], coord[1],
                width=80, height=80,
                output_path=str(output_path)
            )

            if template is not None:
                print(f"   ✅ {template_name}.png")
            else:
                print(f"   ❌ Sikertelen!")

        print("\n✅ Batch capture kész!")
        input("\nNyomj ENTER-t a folytatáshoz...")

    # ===== UTILITY METHODS =====

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

        return coord[0]


def main():
    """Main entry point"""
    print("="*60)
    print("ROK AUTO FARM - SETUP WIZARD COMPLETE")
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
