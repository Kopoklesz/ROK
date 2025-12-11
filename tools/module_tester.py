"""
ROK Auto Farm - Module Tester Framework

Modul-specifikus tesztelés vizualizációval:
- Lépésről-lépésre követés
- Screenshot minden lépésnél
- Kattintások/OCR-ek vizualizálása
- Hiba lokalizálása

Használat:
    python tools/module_tester.py --module training
    python tools/module_tester.py --module gathering
    python tools/module_tester.py --module explorer
"""
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from PIL import ImageGrab, Image, ImageDraw, ImageFont
import cv2
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from library import ImageManager, initialize_game_window, safe_click, press_key
from utils.logger import FarmLogger as log


class ModuleTester:
    """
    Általános module tester keretrendszer

    Funkciók:
    - Screenshot minden lépésnél
    - Vizualizáció (kattintások, OCR régiók)
    - Step-by-step logging
    - Hiba lokalizálás
    """

    def __init__(self, module_name):
        self.module_name = module_name
        self.test_dir = Path(__file__).parent.parent / 'logs' / 'module_tests' / module_name
        self.test_dir.mkdir(parents=True, exist_ok=True)

        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.step_counter = 0

        # Test log
        self.test_log = []

        # Font for visualization
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            self.font = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def start_test(self, description):
        """Test indítása"""
        print("\n" + "="*60)
        print(f"MODULE TEST: {self.module_name.upper()}")
        print(f"Test: {description}")
        print("="*60)

        self.test_log.append({
            'type': 'start',
            'description': description,
            'timestamp': datetime.now().isoformat()
        })

        self.step_counter = 0

    def step(self, description, take_screenshot=True):
        """
        Test lépés

        Args:
            description: Lépés leírása
            take_screenshot: Screenshot készítése
        """
        self.step_counter += 1

        print(f"\n[Step {self.step_counter}] {description}")

        log_entry = {
            'type': 'step',
            'step': self.step_counter,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'screenshot': None
        }

        if take_screenshot:
            screenshot_path = self._take_screenshot(f"step_{self.step_counter:03d}")
            log_entry['screenshot'] = str(screenshot_path)

        self.test_log.append(log_entry)
        time.sleep(0.5)  # Kis delay hogy látszódjon

    def click(self, coords, label="Click"):
        """
        Kattintás + vizualizáció

        Args:
            coords: [x, y] koordináták
            label: Kattintás címke
        """
        print(f"  → Kattintás: {label} @ {coords}")

        # Screenshot ELŐTTE
        screenshot = ImageGrab.grab()
        draw = ImageDraw.Draw(screenshot)

        # Rajzoljuk rá a kattintást
        x, y = coords
        self._draw_click_marker(draw, x, y, label, "red")

        # Mentés
        screenshot_path = self.test_dir / f"{self.timestamp}_step_{self.step_counter:03d}_click_{label.replace(' ', '_')}.png"
        screenshot.save(screenshot_path)

        # Tényleges kattintás
        safe_click(coords)

        self.test_log.append({
            'type': 'click',
            'step': self.step_counter,
            'coords': coords,
            'label': label,
            'screenshot': str(screenshot_path),
            'timestamp': datetime.now().isoformat()
        })

        time.sleep(0.3)

    def ocr_read(self, region, label="OCR"):
        """
        OCR olvasás + vizualizáció

        Args:
            region: OCR régió dict
            label: OCR címke

        Returns:
            str: OCR szöveg
        """
        print(f"  → OCR olvasás: {label} @ region {region}")

        # Screenshot ELŐTTE
        screenshot = ImageGrab.grab()
        draw = ImageDraw.Draw(screenshot)

        # Rajzoljuk rá az OCR régiót
        x = region.get('x', 0)
        y = region.get('y', 0)
        w = region.get('width', 0)
        h = region.get('height', 0)

        draw.rectangle([x, y, x+w, y+h], outline="green", width=3)
        draw.text((x+5, y-20), label, fill="green", font=self.font)

        # OCR olvasás
        ocr_text = ImageManager.read_text_from_region(region, debug_save=False)

        # Eredmény kiírása a képre
        result_text = f"Result: '{ocr_text}'" if ocr_text else "Result: EMPTY"
        draw.text((x+5, y+h+5), result_text, fill="green", font=self.font_small)

        # Mentés
        screenshot_path = self.test_dir / f"{self.timestamp}_step_{self.step_counter:03d}_ocr_{label.replace(' ', '_')}.png"
        screenshot.save(screenshot_path)

        print(f"  → OCR eredmény: '{ocr_text}'")

        self.test_log.append({
            'type': 'ocr',
            'step': self.step_counter,
            'region': region,
            'label': label,
            'result': ocr_text,
            'screenshot': str(screenshot_path),
            'timestamp': datetime.now().isoformat()
        })

        time.sleep(0.3)
        return ocr_text

    def keypress(self, key, label="Keypress"):
        """
        Billentyű lenyomás + log

        Args:
            key: Billentyű ('space', 'esc', stb.)
            label: Címke
        """
        print(f"  → Billentyű: {key} ({label})")

        press_key(key)

        self.test_log.append({
            'type': 'keypress',
            'step': self.step_counter,
            'key': key,
            'label': label,
            'timestamp': datetime.now().isoformat()
        })

        time.sleep(0.3)

    def wait(self, seconds, reason="Waiting"):
        """
        Várakozás

        Args:
            seconds: Másodpercek
            reason: Ok
        """
        print(f"  → Várakozás: {seconds}s ({reason})")

        self.test_log.append({
            'type': 'wait',
            'step': self.step_counter,
            'seconds': seconds,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })

        time.sleep(seconds)

    def error(self, message):
        """
        Hiba jelzés

        Args:
            message: Hiba üzenet
        """
        print(f"\n❌ HIBA: {message}")

        # Screenshot a hiba pillanatában
        screenshot_path = self._take_screenshot(f"step_{self.step_counter:03d}_ERROR")

        self.test_log.append({
            'type': 'error',
            'step': self.step_counter,
            'message': message,
            'screenshot': str(screenshot_path),
            'timestamp': datetime.now().isoformat()
        })

    def success(self, message):
        """
        Siker jelzés

        Args:
            message: Siker üzenet
        """
        print(f"\n✅ SIKER: {message}")

        self.test_log.append({
            'type': 'success',
            'step': self.step_counter,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

    def warning(self, message):
        """
        Figyelmeztetés jelzés

        Args:
            message: Figyelmeztetés üzenet
        """
        print(f"\n⚠️  FIGYELMEZTETÉS: {message}")

        self.test_log.append({
            'type': 'warning',
            'step': self.step_counter,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

    def end_test(self):
        """Test befejezése + riport generálás"""
        print("\n" + "="*60)
        print("TEST BEFEJEZVE")
        print("="*60)

        self.test_log.append({
            'type': 'end',
            'timestamp': datetime.now().isoformat()
        })

        # Log mentése JSON-ba
        log_path = self.test_dir / f"{self.timestamp}_test_log.json"
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_log, f, indent=2, ensure_ascii=False)

        # HTML riport generálás
        self._generate_html_report()

        print(f"\n📊 Test riport:")
        print(f"  - JSON log: {log_path}")
        print(f"  - HTML riport: {self.test_dir / f'{self.timestamp}_report.html'}")
        print(f"  - Screenshot-ok: {self.test_dir}")

    def _take_screenshot(self, suffix):
        """Screenshot készítés"""
        screenshot = ImageGrab.grab()
        screenshot_path = self.test_dir / f"{self.timestamp}_{suffix}.png"
        screenshot.save(screenshot_path)
        return screenshot_path

    def _draw_click_marker(self, draw, x, y, label, color):
        """Kattintás marker rajzolása"""
        size = 25

        # Kereszt
        draw.line([(x-size, y), (x+size, y)], fill=color, width=4)
        draw.line([(x, y-size), (x, y+size)], fill=color, width=4)

        # Kör
        draw.ellipse([x-size, y-size, x+size, y+size], outline=color, width=3)

        # Címke
        draw.text((x+size+10, y-10), label, fill=color, font=self.font)

    def _generate_html_report(self):
        """HTML riport generálás"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Module Test Report - {self.module_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; }}
        .step {{ margin: 20px 0; padding: 15px; border-left: 4px solid #4CAF50; background: #f9f9f9; }}
        .step.error {{ border-left-color: #f44336; }}
        .step-header {{ font-weight: bold; margin-bottom: 10px; }}
        .screenshot {{ max-width: 100%; border: 1px solid #ddd; margin: 10px 0; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
        .ocr-result {{ background: #e8f5e9; padding: 5px; margin: 5px 0; border-radius: 4px; }}
        .click-info {{ background: #e3f2fd; padding: 5px; margin: 5px 0; border-radius: 4px; }}
        .summary {{ background: #fff3e0; padding: 15px; margin: 20px 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Module Test Report: {self.module_name.upper()}</h1>
        <div class="summary">
            <strong>Test futtatva:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
            <strong>Összes lépés:</strong> {self.step_counter}<br>
            <strong>Hibák:</strong> {sum(1 for log in self.test_log if log['type'] == 'error')}
        </div>
"""

        for entry in self.test_log:
            if entry['type'] == 'step':
                html += f"""
        <div class="step">
            <div class="step-header">
                Step {entry['step']}: {entry['description']}
            </div>
            <div class="timestamp">{entry['timestamp']}</div>
"""
                if entry.get('screenshot'):
                    rel_path = Path(entry['screenshot']).name
                    html += f'            <img src="{rel_path}" class="screenshot" alt="Screenshot">\n'

                html += "        </div>\n"

            elif entry['type'] == 'click':
                html += f"""
        <div class="click-info">
            🖱️ Click: {entry['label']} @ {entry['coords']}
        </div>
"""
                if entry.get('screenshot'):
                    rel_path = Path(entry['screenshot']).name
                    html += f'        <img src="{rel_path}" class="screenshot" alt="Click screenshot">\n'

            elif entry['type'] == 'ocr':
                html += f"""
        <div class="ocr-result">
            📖 OCR: {entry['label']} → Result: '{entry.get('result', 'EMPTY')}'
        </div>
"""
                if entry.get('screenshot'):
                    rel_path = Path(entry['screenshot']).name
                    html += f'        <img src="{rel_path}" class="screenshot" alt="OCR screenshot">\n'

            elif entry['type'] == 'error':
                html += f"""
        <div class="step error">
            <div class="step-header">❌ HIBA</div>
            <div>{entry['message']}</div>
            <div class="timestamp">{entry['timestamp']}</div>
"""
                if entry.get('screenshot'):
                    rel_path = Path(entry['screenshot']).name
                    html += f'            <img src="{rel_path}" class="screenshot" alt="Error screenshot">\n'

                html += "        </div>\n"

        html += """
    </div>
</body>
</html>
"""

        report_path = self.test_dir / f"{self.timestamp}_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)


# ===== MODUL-SPECIFIKUS TESZTEREK =====

class TrainingTester(ModuleTester):
    """Training module tester"""

    def __init__(self):
        super().__init__('training')
        self.config_dir = Path(__file__).parent.parent / 'config'

    def run_full_test(self):
        """Teljes training teszt"""
        self.start_test("Training Manager Full Test")

        try:
            # Load configs
            self.step("Config betöltése")
            training_coords = self._load_config('training_coords.json')
            training_regions = self._load_config('training_time_regions.json')

            if not training_coords:
                self.error("training_coords.json hiányzik!")
                self.end_test()
                return

            # Check if OCR regions are configured
            ocr_available = False
            if training_regions:
                # Check if any region has valid x,y coordinates (not 0,0)
                for key, region in training_regions.items():
                    if isinstance(region, dict) and region.get('x', 0) != 0:
                        ocr_available = True
                        break

            if not ocr_available:
                self.warning("⚠️ OCR régiók nincsenek beállítva - OCR tesztek kihagyva")
                self.warning("   Csak koordináta kattintások lesznek vizualizálva")

            # Step 1: Panel megnyitás
            self.step("Training panel megnyitása")
            open_panel = training_coords.get('open_panel', [0, 0])
            if open_panel != [0, 0]:
                self.click(open_panel, "Open Panel")
                self.wait(2, "Panel betöltés")

            # Step 2: Buildings OCR (only if OCR regions available)
            if ocr_available:
                buildings = ['barracks', 'archery', 'stable', 'siege']
                for building in buildings:
                    self.step(f"{building.upper()} OCR olvasása")

                    region_key = f"{building}_time"
                    region = training_regions.get(region_key)

                    if region and region.get('x', 0) != 0:
                        ocr_text = self.ocr_read(region, f"{building.upper()} Time")

                        if ocr_text:
                            self.success(f"{building.upper()} OCR OK: '{ocr_text}'")
                        else:
                            self.warning(f"{building.upper()} OCR üres (lehet nincs training)")
                    else:
                        self.warning(f"{building.upper()} OCR régió nincs beállítva - skip")
            else:
                self.step("OCR tesztek kihagyva (régiók nincsenek beállítva)")

            # Step 3: Panel bezárás
            self.step("Training panel bezárása")
            close_panel = training_coords.get('close_panel', [0, 0])
            if close_panel != [0, 0]:
                self.click(close_panel, "Close Panel")
                self.wait(1, "Panel bezárás")

            # Step 4: Clean state
            self.step("Clean state (2x SPACE)")
            self.keypress('space', "Kigugrás városból")
            self.wait(1, "SPACE #1 után")
            self.keypress('space', "Visszaugrás városba")
            self.wait(1, "SPACE #2 után")

            self.success("Training teszt sikeresen befejezve!")

        except Exception as e:
            self.error(f"Exception: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.end_test()

    def _load_config(self, filename):
        """Config betöltés"""
        filepath = self.config_dir / filename
        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


class GatheringTester(ModuleTester):
    """Gathering module tester"""

    def __init__(self):
        super().__init__('gathering')
        self.config_dir = Path(__file__).parent.parent / 'config'

    def run_full_test(self):
        """Teljes gathering teszt"""
        self.start_test("Gathering Manager Full Test")

        try:
            # Load configs
            self.step("Config betöltése")
            gathering_coords = self._load_config('gathering_coords.json')
            resource_regions = self._load_config('farm_regions.json')

            if not gathering_coords or not resource_regions:
                self.error("Config fájlok hiányoznak!")
                self.end_test()
                return

            # Step 1: Resource OCR (Home screen)
            self.step("Resource OCR (Home screen)")

            resources = ['wheat', 'wood', 'stone', 'gold']
            for resource in resources:
                region = resource_regions.get(resource)
                if region:
                    ocr_text = self.ocr_read(region, f"{resource.upper()}")
                    if ocr_text:
                        self.success(f"{resource.upper()} OCR OK: '{ocr_text}'")
                    else:
                        self.error(f"{resource.upper()} OCR üres!")

            # Step 2: Map button
            self.step("Map button kattintás")
            map_button = gathering_coords.get('map_button', [0, 0])
            if map_button != [0, 0]:
                self.click(map_button, "Map Button")
                self.wait(3, "Térkép betöltés")

            # Step 3: Search button
            self.step("Search button kattintás")
            search_button = gathering_coords.get('search_button', [0, 0])
            if search_button != [0, 0]:
                self.click(search_button, "Search Button")
                self.wait(2, "Search panel betöltés")

            # Step 4: Clean state
            self.step("Clean state (2x SPACE)")
            self.keypress('space', "Kigugrás térképről")
            self.wait(1, "SPACE #1 után")
            self.keypress('space', "Visszaugrás városba")
            self.wait(1, "SPACE #2 után")

            self.success("Gathering teszt sikeresen befejezve!")

        except Exception as e:
            self.error(f"Exception: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.end_test()

    def _load_config(self, filename):
        """Config betöltés"""
        filepath = self.config_dir / filename
        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


class ExplorerTester(ModuleTester):
    """Explorer module tester"""

    def __init__(self):
        super().__init__('explorer')
        self.config_dir = Path(__file__).parent.parent / 'config'

    def run_full_test(self):
        """Teljes explorer teszt - követi az explorer.py workflow-t"""
        self.start_test("Explorer Manager Full Test")

        try:
            # Load config
            self.step("Config betöltése")
            explorer_coords = self._load_config('explorer_coords.json')

            if not explorer_coords:
                self.error("explorer_coords.json hiányzik!")
                self.end_test()
                return

            # Check if OCR regions are configured
            ocr_available = False
            ocr_regions = ['exploration_region_1', 'exploration_region_2', 'exploration_region_3']
            for region_key in ocr_regions:
                region = explorer_coords.get(region_key)
                if isinstance(region, dict) and region.get('x', 0) != 0:
                    ocr_available = True
                    break

            if not ocr_available:
                self.warning("⚠️ Exploration OCR régiók nincsenek beállítva - OCR tesztek kihagyva")
                self.warning("   Csak koordináta kattintások lesznek vizualizálva")

            # ===== STEP 1: CHECK EXPLORATION (like check_exploration() in explorer.py) =====
            self.step("Check Exploration - Que menü megnyitása")
            open_queue = explorer_coords.get('open_queue_menu', [0, 0])
            if open_queue != [0, 0]:
                self.click(open_queue, "Open Queue Menu")
                self.wait(2, "Queue menü betöltés")

            self.step("Check Exploration - Que fül bezárása")
            close_queue_tab = explorer_coords.get('close_queue_tab', [0, 0])
            if close_queue_tab != [0, 0]:
                self.click(close_queue_tab, "Close Queue Tab")
                self.wait(1, "Queue tab bezárás")

            self.step("Check Exploration - Scout fül megnyitása")
            open_scout_tab = explorer_coords.get('open_scout_tab', [0, 0])
            if open_scout_tab != [0, 0]:
                self.click(open_scout_tab, "Open Scout Tab")
                self.wait(2, "Scout tab betöltés")

            # OCR reading (if available)
            if ocr_available:
                self.step("Check Exploration - Felfedezés % OCR olvasás")
                for i, region_key in enumerate(ocr_regions, 1):
                    region = explorer_coords.get(region_key)
                    if region and region.get('x', 0) != 0:
                        ocr_text = self.ocr_read(region, f"Exploration Region {i}")
                        if ocr_text:
                            self.success(f"Region {i} OCR OK: '{ocr_text}'")
                        else:
                            self.warning(f"Region {i} OCR üres")
                    else:
                        self.warning(f"Region {i} nincs beállítva")
            else:
                self.step("Exploration OCR olvasás kihagyva (régiók nincsenek beállítva)")

            self.step("Check Exploration - Scout bezárása")
            close_scout = explorer_coords.get('close_scout', [0, 0])
            if close_scout != [0, 0]:
                self.click(close_scout, "Close Scout")
                self.wait(1, "Scout bezárás")

            self.step("Check Exploration - Que fül megnyitása")
            open_queue_tab = explorer_coords.get('open_queue_tab', [0, 0])
            if open_queue_tab != [0, 0]:
                self.click(open_queue_tab, "Open Queue Tab")
                self.wait(1, "Queue tab megnyitás")

            self.step("Check Exploration - Que menü bezárása")
            close_queue = explorer_coords.get('close_queue_menu', [0, 0])
            if close_queue != [0, 0]:
                self.click(close_queue, "Close Queue Menu")
                self.wait(1, "Queue menü bezárás")

            # ===== STEP 2: START EXPLORATION (like start_exploration() in explorer.py) =====
            self.step("Start Exploration - Scout épület kattintás")
            scout_building = explorer_coords.get('scout_building', [0, 0])
            if scout_building != [0, 0]:
                self.click(scout_building, "Scout Building")
                self.wait(2, "Scout building megnyitás")

            self.step("Start Exploration - Pre-explore gomb")
            pre_explore = explorer_coords.get('pre_explore_button', [0, 0])
            if pre_explore != [0, 0]:
                self.click(pre_explore, "Pre-explore Button")
                self.wait(1, "Pre-explore")

            self.step("Start Exploration - Explore gomb (1. kattintás)")
            explore_button = explorer_coords.get('explore_button', [0, 0])
            if explore_button != [0, 0]:
                self.click(explore_button, "Explore Button (1st)")
                self.wait(1.5, "Fix 1.5 mp várakozás")

            self.step("Start Exploration - Explore gomb (2. kattintás)")
            if explore_button != [0, 0]:
                self.click(explore_button, "Explore Button (2nd)")
                self.wait(1, "Explore után")

            # Additional click before clean state (screen center or confirm)
            self.step("Start Exploration - Fix kattintás (képernyő közép)")
            screen_center = explorer_coords.get('screen_center', [0, 0])
            if screen_center != [0, 0]:
                self.click(screen_center, "Screen Center")
                self.wait(1, "Fix kattintás után")

            # ===== STEP 3: CLEAN STATE =====
            self.step("Clean state (2x SPACE)")
            self.keypress('space', "SPACE (1.)")
            self.wait(1, "SPACE #1 után")
            self.keypress('space', "SPACE (2.)")
            self.wait(1, "SPACE #2 után")

            self.success("Explorer teszt sikeresen befejezve!")

        except Exception as e:
            self.error(f"Exception: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.end_test()

    def _load_config(self, filename):
        """Config betöltés"""
        filepath = self.config_dir / filename
        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


# ===== MAIN =====

def main():
    parser = argparse.ArgumentParser(description='ROK Module Tester')
    parser.add_argument('--module', choices=['training', 'gathering', 'explorer', 'alliance'],
                        required=True, help='Module to test')

    args = parser.parse_args()

    # Initialize game window
    print("Játék ablak inicializálás...")
    if not initialize_game_window("BlueStacks"):
        print("❌ Játék ablak nem található!")
        return
    print("✅ Játék ablak OK\n")

    # Run test
    if args.module == 'training':
        tester = TrainingTester()
        tester.run_full_test()
    elif args.module == 'gathering':
        tester = GatheringTester()
        tester.run_full_test()
    elif args.module == 'explorer':
        tester = ExplorerTester()
        tester.run_full_test()
    else:
        print(f"❌ Module '{args.module}' not implemented yet")


if __name__ == "__main__":
    main()
