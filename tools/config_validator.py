"""
ROK Auto Farm - Config Validator & Visualizer

Funkciók:
1. Vizualizálja az összes koordinátát/régiót a képernyőn
2. Ellenőrzi hogy minden config rendben van-e
3. Teszteli az OCR régiókat
4. Koordináta pontosság validáció

Használat:
    python tools/config_validator.py --mode [visual|check|ocr|all]
"""
import sys
import json
import time
import argparse
from pathlib import Path
from PIL import ImageGrab, Image, ImageDraw, ImageFont
import cv2
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from library import ImageManager, initialize_game_window
from utils.logger import FarmLogger as log


class ConfigValidator:
    """Config validátor és vizualizáló"""

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / 'config'
        self.errors = []
        self.warnings = []

    def load_config(self, filename):
        """Config fájl betöltése"""
        filepath = self.config_dir / filename
        if not filepath.exists():
            self.errors.append(f"❌ {filename} nem található!")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.errors.append(f"❌ {filename} betöltési hiba: {e}")
            return None

    def validate_all_configs(self):
        """Összes config validálása"""
        print("="*60)
        print("CONFIG VALIDÁCIÓ")
        print("="*60)

        # Settings
        settings = self.load_config('settings.json')
        if settings:
            print("✅ settings.json")
            self._validate_settings(settings)

        # Training
        training_coords = self.load_config('training_coords.json')
        if training_coords:
            print("✅ training_coords.json")
            self._validate_training_coords(training_coords)

        training_regions = self.load_config('training_time_regions.json')
        if training_regions:
            print("✅ training_time_regions.json")
            self._validate_regions(training_regions, "Training")

        # Gathering
        gathering_coords = self.load_config('gathering_coords.json')
        if gathering_coords:
            print("✅ gathering_coords.json")

        # Resource regions
        resource_regions = self.load_config('resource_regions.json')
        if resource_regions:
            print("✅ resource_regions.json")
            self._validate_regions(resource_regions, "Resource")

        # Alliance
        alliance_coords = self.load_config('alliance_coords.json')
        if alliance_coords:
            print("✅ alliance_coords.json")

        print("\n" + "="*60)
        print("VALIDÁCIÓ EREDMÉNY")
        print("="*60)

        if self.errors:
            print(f"\n❌ HIBÁK ({len(self.errors)} db):")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n⚠️  FIGYELMEZTETÉSEK ({len(self.warnings)} db):")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ Minden config rendben!")

        return len(self.errors) == 0

    def _validate_settings(self, settings):
        """Settings validálás"""
        required = ['gathering', 'training', 'alliance', 'anti_afk', 'human_wait']
        for key in required:
            if key not in settings:
                self.warnings.append(f"⚠️  settings.json: '{key}' hiányzik")

    def _validate_training_coords(self, coords):
        """Training koordináták validálása"""
        required = ['open_panel', 'close_panel']
        for key in required:
            if key not in coords or coords[key] == [0, 0]:
                self.warnings.append(f"⚠️  training_coords.json: '{key}' nincs beállítva")

        # Buildings check
        buildings = ['barracks', 'archery', 'stable', 'siege']
        for building in buildings:
            if building not in coords:
                self.warnings.append(f"⚠️  training_coords.json: '{building}' hiányzik")
                continue

            building_coords = coords[building]
            required_keys = ['building', 'button', 'tier', 'confirm', 'troop_gather']
            for key in required_keys:
                if key not in building_coords or building_coords[key] == [0, 0]:
                    self.warnings.append(f"⚠️  training_coords.json: '{building}.{key}' nincs beállítva")

    def _validate_regions(self, regions, name):
        """OCR régiók validálása"""
        for region_name, region in regions.items():
            if not region or not isinstance(region, dict):
                self.warnings.append(f"⚠️  {name} regions: '{region_name}' rossz formátum")
                continue

            required = ['x', 'y', 'width', 'height']
            for key in required:
                if key not in region or region[key] == 0:
                    self.warnings.append(f"⚠️  {name} regions: '{region_name}.{key}' nincs beállítva")

    def visualize_coordinates(self, coord_type='all'):
        """
        Koordináták vizualizálása a képernyőn

        Args:
            coord_type: 'training' | 'gathering' | 'alliance' | 'all'
        """
        print("\n" + "="*60)
        print("KOORDINÁTA VIZUALIZÁCIÓ")
        print("="*60)
        print("Készíts egy screenshot-ot...")

        time.sleep(2)

        # Screenshot
        screenshot = ImageGrab.grab()
        draw = ImageDraw.Draw(screenshot)

        # Font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            font = ImageFont.load_default()

        # Training koordináták
        if coord_type in ['training', 'all']:
            training_coords = self.load_config('training_coords.json')
            if training_coords:
                self._draw_training_coords(draw, training_coords, font)

        # Gathering koordináták
        if coord_type in ['gathering', 'all']:
            gathering_coords = self.load_config('gathering_coords.json')
            if gathering_coords:
                self._draw_gathering_coords(draw, gathering_coords, font)

        # Alliance koordináták
        if coord_type in ['alliance', 'all']:
            alliance_coords = self.load_config('alliance_coords.json')
            if alliance_coords:
                self._draw_alliance_coords(draw, alliance_coords, font)

        # Mentés
        output_path = Path(__file__).parent.parent / 'logs' / 'config_visualization.png'
        screenshot.save(output_path)

        print(f"✅ Vizualizáció mentve: {output_path}")
        print("   Nyisd meg a képet hogy lásd a koordinátákat!")

        # Megjelenítés (ha van display)
        try:
            screenshot.show()
        except:
            pass

    def _draw_training_coords(self, draw, coords, font):
        """Training koordináták rajzolása"""
        # Panel open/close
        self._draw_point(draw, coords.get('open_panel', [0,0]), "Panel Open", "red", font)
        self._draw_point(draw, coords.get('close_panel', [0,0]), "Panel Close", "red", font)

        # Buildings
        buildings = ['barracks', 'archery', 'stable', 'siege']
        colors = ['blue', 'green', 'purple', 'orange']

        for building, color in zip(buildings, colors):
            if building not in coords:
                continue

            building_coords = coords[building]
            prefix = building.upper()[:3]

            self._draw_point(draw, building_coords.get('building', [0,0]), f"{prefix} Building", color, font)
            self._draw_point(draw, building_coords.get('button', [0,0]), f"{prefix} Button", color, font)
            self._draw_point(draw, building_coords.get('tier', [0,0]), f"{prefix} Tier", color, font)
            self._draw_point(draw, building_coords.get('confirm', [0,0]), f"{prefix} Confirm", color, font)
            self._draw_point(draw, building_coords.get('troop_gather', [0,0]), f"{prefix} Gather", color, font)

    def _draw_gathering_coords(self, draw, coords, font):
        """Gathering koordináták rajzolása"""
        # Map button
        self._draw_point(draw, coords.get('map_button', [0,0]), "Map Button", "cyan", font)

        # Search button
        self._draw_point(draw, coords.get('search_button', [0,0]), "Search", "cyan", font)

    def _draw_alliance_coords(self, draw, coords, font):
        """Alliance koordináták rajzolása"""
        self._draw_point(draw, coords.get('alliance_button', [0,0]), "Alliance", "yellow", font)
        self._draw_point(draw, coords.get('help_button', [0,0]), "Help", "yellow", font)

    def _draw_point(self, draw, coords, label, color, font):
        """Pont rajzolása kereszttel + címkével"""
        if not coords or coords == [0, 0]:
            return

        x, y = coords
        size = 20

        # Kereszt rajzolása
        draw.line([(x-size, y), (x+size, y)], fill=color, width=3)
        draw.line([(x, y-size), (x, y+size)], fill=color, width=3)

        # Kör
        draw.ellipse([x-size, y-size, x+size, y+size], outline=color, width=2)

        # Címke
        draw.text((x+size+5, y-10), label, fill=color, font=font)

    def visualize_ocr_regions(self, region_type='all'):
        """
        OCR régiók vizualizálása

        Args:
            region_type: 'training' | 'resource' | 'gathering' | 'all'
        """
        print("\n" + "="*60)
        print("OCR RÉGIÓ VIZUALIZÁCIÓ")
        print("="*60)
        print("Készíts egy screenshot-ot...")

        time.sleep(2)

        # Screenshot
        screenshot = ImageGrab.grab()
        draw = ImageDraw.Draw(screenshot)

        # Font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except:
            font = ImageFont.load_default()

        # Training régiók
        if region_type in ['training', 'all']:
            training_regions = self.load_config('training_time_regions.json')
            if training_regions:
                self._draw_regions(draw, training_regions, font, "red")

        # Resource régiók
        if region_type in ['resource', 'all']:
            resource_regions = self.load_config('resource_regions.json')
            if resource_regions:
                self._draw_regions(draw, resource_regions, font, "green")

        # Mentés
        output_path = Path(__file__).parent.parent / 'logs' / 'ocr_regions_visualization.png'
        screenshot.save(output_path)

        print(f"✅ OCR régió vizualizáció mentve: {output_path}")
        print("   Nyisd meg a képet hogy lásd a régiókat!")

        # Megjelenítés
        try:
            screenshot.show()
        except:
            pass

    def _draw_regions(self, draw, regions, font, color):
        """OCR régiók rajzolása"""
        for region_name, region in regions.items():
            if not region or not isinstance(region, dict):
                continue

            x = region.get('x', 0)
            y = region.get('y', 0)
            w = region.get('width', 0)
            h = region.get('height', 0)

            if x == 0 or y == 0:
                continue

            # Téglalap
            draw.rectangle([x, y, x+w, y+h], outline=color, width=2)

            # Címke
            draw.text((x+5, y-20), region_name, fill=color, font=font)

    def test_ocr_regions(self):
        """OCR régiók tesztelése"""
        print("\n" + "="*60)
        print("OCR RÉGIÓ TESZT")
        print("="*60)

        # Training régiók
        print("\nTraining time régiók:")
        training_regions = self.load_config('training_time_regions.json')
        if training_regions:
            for region_name, region in training_regions.items():
                if not region or region.get('x', 0) == 0:
                    print(f"  ⚠️  {region_name}: Nincs beállítva")
                    continue

                ocr_text = ImageManager.read_text_from_region(region)
                if ocr_text:
                    print(f"  ✅ {region_name}: '{ocr_text}'")
                else:
                    print(f"  ⚠️  {region_name}: Üres OCR")

        # Resource régiók
        print("\nResource régiók:")
        resource_regions = self.load_config('resource_regions.json')
        if resource_regions:
            for region_name, region in resource_regions.items():
                if not region or region.get('x', 0) == 0:
                    print(f"  ⚠️  {region_name}: Nincs beállítva")
                    continue

                ocr_text = ImageManager.read_text_from_region(region)
                if ocr_text:
                    print(f"  ✅ {region_name}: '{ocr_text}'")
                else:
                    print(f"  ⚠️  {region_name}: Üres OCR")


def main():
    parser = argparse.ArgumentParser(description='ROK Config Validator & Visualizer')
    parser.add_argument('--mode', choices=['check', 'visual-coords', 'visual-ocr', 'test-ocr', 'all'],
                        default='all', help='Teszt mód')
    parser.add_argument('--type', choices=['training', 'gathering', 'alliance', 'resource', 'all'],
                        default='all', help='Config típus')

    args = parser.parse_args()

    # Initialize
    validator = ConfigValidator()

    # Game window init
    if args.mode != 'check':
        print("Játék ablak inicializálás...")
        if not initialize_game_window("BlueStacks"):
            print("❌ Játék ablak nem található!")
            return
        print("✅ Játék ablak OK\n")

    # Check mode
    if args.mode in ['check', 'all']:
        validator.validate_all_configs()

    # Visual coords mode
    if args.mode in ['visual-coords', 'all']:
        validator.visualize_coordinates(args.type)

    # Visual OCR mode
    if args.mode in ['visual-ocr', 'all']:
        validator.visualize_ocr_regions(args.type)

    # Test OCR mode
    if args.mode in ['test-ocr', 'all']:
        validator.test_ocr_regions()


if __name__ == "__main__":
    main()
