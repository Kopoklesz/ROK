"""
Auto Farm - Base Farm
Közös farm logika minden típushoz
"""
import time
import json
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from library import (
    safe_click, press_key, wait_random, get_screen_center,
    ImageManager
)
from utils.logger import FarmLogger as log
from utils.time_utils import parse_time, format_time


class BaseFarm:
    """Alap farm osztály - közös logika"""
    
    def __init__(self, farm_type, config_dir):
        """
        Args:
            farm_type: 'wheat', 'wood', 'stone', 'gold'
            config_dir: Config könyvtár path
        """
        self.farm_type = farm_type
        self.config_dir = Path(config_dir)
        
        # Konfigurációk betöltése
        self.settings = self._load_settings()
        self.coords = self._load_coordinates()
        self.time_regions = self._load_time_regions()
        
        # Paraméterek
        self.repeat_count = self.settings.get('repeat_count', 4)
        self.human_wait_min = self.settings.get('human_wait_min', 3)
        self.human_wait_max = self.settings.get('human_wait_max', 8)
        self.gather_retry = self.settings.get('gather_retry_attempts', 25)
        self.default_march_time = self.settings.get('default_march_time', 60)
        self.default_gather_time = self.settings.get('default_gather_time', 5400)
    
    def _load_settings(self):
        """Settings.json betöltése"""
        settings_file = self.config_dir / 'settings.json'
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_coordinates(self):
        """Farm koordináták betöltése"""
        coords_file = self.config_dir / 'farm_coords.json'
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                all_coords = json.load(f)
                return all_coords.get(self.farm_type, {})
        return {}
    
    def _load_time_regions(self):
        """Idő OCR régiók betöltése"""
        time_file = self.config_dir / 'time_regions.json'
        if time_file.exists():
            with open(time_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def run(self):
        """Teljes farm ciklus futtatása"""
        log.separator('=', 60)
        log.info(f"🌾 {self.farm_type.upper()} FARM INDÍTÁSA")
        log.separator('=', 60)
        
        collected_times = []
        
        for i in range(self.repeat_count):
            log.separator('-', 60)
            log.info(f"🔄 Farm iteráció {i+1}/{self.repeat_count}")
            log.separator('-', 60)
            
            # 1. SPACE
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp (emberi faktor)")
            time.sleep(delay)
            log.action("SPACE billentyű lenyomása")
            press_key('space')
            
            # 2. F
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("B billentyű lenyomása (térkép megnyitás)")
            press_key('b')
            
            # 3. NYERSANYAG SELECT
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = self.coords.get('resource_icon', [0, 0])
            log.click(f"{self.farm_type.upper()} alapanyag kiválasztása → ({coords[0]}, {coords[1]})")
            safe_click(coords)
            
            # 4. FARM POZÍCIÓ 1
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = self.coords.get('level_button', [0, 0])
            log.click(f"Farm pozíció #1 → ({coords[0]}, {coords[1]})")
            safe_click(coords)
            
            # 5. FARM POZÍCIÓ 2
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = self.coords.get('search_button', [0, 0])
            log.click(f"Farm pozíció #2 → ({coords[0]}, {coords[1]})")
            safe_click(coords)
            
            # 6. GATHER.PNG KERESÉS
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.search("Gather.png gomb keresése (threshold: 0.7)...")
            
            gather_coords = self.find_gather_button()
            
            if not gather_coords:
                log.error("Gather gomb nem található 25 próba után!")
                log.action("SPACE lenyomása → Farm restart")
                press_key('space')
                return "RESTART"
            
            log.success(f"Gather gomb megtalálva → ({gather_coords[0]}, {gather_coords[1]})")
            log.click("Kattintás a Gather gombra")
            safe_click(gather_coords)
            
            # 7. CONFIRM
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = self.coords.get('new_troops', [0, 0])
            log.click(f"Megerősítés gomb → ({coords[0]}, {coords[1]})")
            safe_click(coords)
            
            # 8. IDŐ A KIOLVASÁS (MARCH TIME)
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            region = self.time_regions.get('march_time', {})
            log.ocr(f"March Time (Idő A) kiolvasása → Region: (x:{region.get('x',0)}, y:{region.get('y',0)}, w:{region.get('width',0)}, h:{region.get('height',0)})")
            
            march_time = self.read_time('march_time')
            
            if march_time is None:
                march_time = self.default_march_time
                log.warning(f"March Time nem olvasható! Default érték: {march_time} sec ({format_time(march_time)})")
            else:
                log.success(f"March Time sikeresen kiolvasva: {format_time(march_time)} ({march_time} sec)")
            
            # 9. FIX KOORDINÁTA
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = self.coords.get('march_button', [0, 0])
            log.click(f"Fix koordináta kattintás → ({coords[0]}, {coords[1]})")
            safe_click(coords)
            
            # 10. VÁRNI A IDŐ + 1 SEC
            wait_duration = march_time + 1
            log.wait(f"Várakozás {wait_duration} sec (A idő + 1 sec) = {format_time(wait_duration)}")
            time.sleep(wait_duration)
            
            # 11. KÉPERNYŐ KÖZEPE
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            screen_center = get_screen_center()
            coords = self.coords.get('screen_center', screen_center)
            log.click(f"Képernyő közép kattintás → ({coords[0]}, {coords[1]})")
            safe_click(coords)
            
            # 12. IDŐ B KIOLVASÁS
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)

            region = self.time_regions.get('gather_time', {})
            log.ocr(f"Idő B kiolvasása → Region: (x:{region.get('x',0)}, y:{region.get('y',0)}, "
                    f"w:{region.get('width',0)}, h:{region.get('height',0)})")

            gather_time = None
            for attempt in range(30):
                gather_time = self.read_time('gather_time')
                if gather_time is not None:
                    log.success(f"Idő B sikeresen kiolvasva {attempt+1}. próbálkozásra: "
                                f"{format_time(gather_time)} ({gather_time} sec)")
                    break
                log.warning(f"Idő B nem olvasható ({attempt+1}/30), újrapróbálkozás...")
                time.sleep(0.5)

            if gather_time is None:
                gather_time = self.default_gather_time
                log.warning(f"Idő B nem olvasható 30 próbálkozás után sem! "
                            f"Default érték: {gather_time} sec ({format_time(gather_time)})")

            # 14. C_i SZÁMÍTÁS
            C_i = march_time + gather_time
            collected_times.append(C_i)
            
            log.success(f"C{i+1} idő kiszámítva: {format_time(march_time)} + {format_time(gather_time)} = {format_time(C_i)} ({C_i} sec)")
            
            # 15. SPACE
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("SPACE lenyomása (C idő mentése után)")
            press_key('space')
            
            log.separator('-', 60)
        
        # 15. MAX IDŐ + 1 PERC
        log.separator('=', 60)
        log.info("📊 Összes C idő kiértékelése")
        log.separator('=', 60)
        
        for idx, c_time in enumerate(collected_times, 1):
            log.info(f"C{idx} = {format_time(c_time)} ({c_time} sec)")
        
        max_time = max(collected_times)
        wait_time = max_time + 60
        
        log.success(f"Leghosszabb idő: {format_time(max_time)}")
        log.info(f"Várakozási idő: {format_time(max_time)} + 1 perc = {format_time(wait_time)}")
        
        log.wait(f"Várakozás {wait_time} sec ({format_time(wait_time)}) a következő farm ciklusig...")
        time.sleep(wait_time)
        
        log.separator('=', 60)
        log.success(f"{self.farm_type.upper()} farm ciklus befejezve!")
        log.separator('=', 60)
        
        return "SUCCESS"
    
    def find_gather_button(self):
        """Gather.png keresés 25x retry-val"""
        images_dir = Path(__file__).parent.parent / 'images'
        gather_path = images_dir / 'gather.png'
        
        for attempt in range(self.gather_retry):
            log.search(f"Gather.png keresése... ({attempt+1}/{self.gather_retry})")
            
            coords = ImageManager.find_image(str(gather_path), threshold=0.7)
            
            if coords:
                log.success(f"Gather.png megtalálva {attempt+1}. próbálkozásra → ({coords[0]}, {coords[1]})")
                return coords
            
            log.warning(f"Gather.png nem található ({attempt+1}/{self.gather_retry}), újrapróbálkozás...")
            time.sleep(0.5)
        
        return None
    
    def read_time(self, time_key):
        """Idő kiolvasás OCR-rel"""
        region = self.time_regions.get(time_key, {})
        
        if not region:
            return None
        
        ocr_text = ImageManager.read_text_from_region(region)
        
        if not ocr_text:
            return None
        
        time_sec = parse_time(ocr_text)
        return time_sec