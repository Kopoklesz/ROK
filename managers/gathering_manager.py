"""
Auto Farm - Gathering Manager
Commander-based farmolás timer rendszerrel
"""
import json
import time
import random
from pathlib import Path

from library import ImageManager, safe_click, press_key, wait_random, get_screen_center
from utils.logger import FarmLogger as log
from utils.ocr_parser import parse_resource_value
from utils.time_utils import parse_time, format_time
from utils.timer_manager import timer_manager
from utils.queue_manager import queue_manager

from farms.base_farm import BaseFarm


class GatheringManager:
    """Commander-based gathering manager"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / 'config'
        
        # Config betöltés
        self.settings = self._load_settings()
        self.farm_regions = self._load_farm_regions()
        
        # Commander config
        self.max_commanders = self.settings.get('gathering', {}).get('max_commanders', 4)
        self.commanders = self.settings.get('gathering', {}).get('commanders', [])
        
        # Human wait
        human_wait = self.settings.get('human_wait', {})
        self.human_wait_min = human_wait.get('min_seconds', 5)
        self.human_wait_max = human_wait.get('max_seconds', 10)
        
        # Defaults
        defaults = self.settings.get('defaults', {})
        self.default_march_time = defaults.get('march_time_seconds', 300)
        self.default_gather_time = defaults.get('gather_time_seconds', 5400)
        
        # Base farm instance-ok (resource típusonként)
        self.farms = {
            'wheat': BaseFarm('wheat', self.config_dir),
            'wood': BaseFarm('wood', self.config_dir),
            'stone': BaseFarm('stone', self.config_dir),
            'gold': BaseFarm('gold', self.config_dir)
        }
    
    def _load_settings(self):
        """Settings.json betöltése"""
        settings_file = self.config_dir / 'settings.json'
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_farm_regions(self):
        """Farm regions betöltése"""
        regions_file = self.config_dir / 'farm_regions.json'
        if regions_file.exists():
            with open(regions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def initial_start_all_commanders(self):
        """
        Első indulás: összes enabled commander queue-ba
        """
        log.separator('=', 60)
        log.info("Gathering Manager: Commanders első indítása")
        log.separator('=', 60)
        
        for commander in self.commanders:
            commander_id = commander.get('id')
            enabled = commander.get('enabled', True)
            
            if enabled:
                task_id = f"commander_{commander_id}_start"
                queue_manager.add_task(task_id, "gathering", {"commander_id": commander_id})
                log.success(f"Commander #{commander_id} queue-ba téve (start)")
        
        log.separator('=', 60)
    
    def run_commander(self, commander_id, task_data=None):
        """
        Egyetlen commander futtatása
        
        Args:
            commander_id: Commander azonosító (1-4)
            task_data: Task extra adat
            
        Returns:
            str: "SUCCESS" vagy "RESTART"
        """
        log.separator('=', 60)
        log.info(f"🌾 COMMANDER #{commander_id} - GATHERING START")
        log.separator('=', 60)
        
        # 1. Resource OCR
        resources = self._read_all_resources()
        
        if not resources:
            log.error("Nincs beállított erőforrás régió!")
            return "RESTART"
        
        # 2. Minimum resource kiválasztás
        selected_resource = self._select_minimum_resource(resources)
        
        log.success(f"Commander #{commander_id} → {selected_resource.upper()} farmolás")
        
        # 3. Farm instance
        farm = self.farms.get(selected_resource)
        
        if not farm:
            log.error(f"Farm instance nem található: {selected_resource}")
            return "RESTART"
        
        # 4. Farm process futtatása (EGYSZER!)
        result = self._run_single_farm_cycle(farm, commander_id)
        
        if result == "RESTART":
            log.warning(f"Commander #{commander_id} restart szükséges!")
            return "RESTART"
        
        # 5. Timer beállítása
        march_time = result.get('march_time', self.default_march_time)
        gather_time = result.get('gather_time', self.default_gather_time)
        total_time = march_time + gather_time
        
        log.info(f"Commander #{commander_id} - Össz idő: {format_time(total_time)} ({total_time} sec)")
        
        # Timer hozzáadás
        timer_id = f"commander_{commander_id}"
        task_id = f"commander_{commander_id}_restart"
        
        timer_manager.add_timer(
            timer_id=timer_id,
            deadline_seconds=total_time,
            task_id=task_id,
            task_type="gathering",
            data={"commander_id": commander_id}
        )
        
        log.success(f"Commander #{commander_id} timer beállítva: {format_time(total_time)} múlva restart")
        log.separator('=', 60)
        
        return "SUCCESS"
    
    def _read_all_resources(self):
        """Összes erőforrás OCR kiolvasása"""
        log.info("📊 Erőforrások kiolvasása...")
        
        resources = {}
        
        for resource_name, region in self.farm_regions.items():
            if region is None:
                continue
            
            ocr_text = ImageManager.read_text_from_region(region)
            value = parse_resource_value(ocr_text)
            resources[resource_name] = value
            
            log.info(f"  {resource_name.upper()}: {ocr_text} → {value:,}")
        
        return resources
    
    def _select_minimum_resource(self, resources):
        """Legkisebb erőforrás kiválasztása (osztással)"""
        log.info("🧮 Erőforrás értékelés...")
        
        values = {}
        for res, amount in resources.items():
            if res == 'wheat' or res == 'wood':
                divisor = 4
            elif res == 'stone':
                divisor = 3
            elif res == 'gold':
                divisor = 2
            else:
                divisor = 1
            
            values[res] = amount / divisor
            log.info(f"  {res.upper()}: {amount:,} ÷ {divisor} = {values[res]:,.1f}")
        
        min_resource = min(values, key=values.get)
        log.success(f"  Minimum: {min_resource.upper()} ({values[min_resource]:,.1f})")
        
        return min_resource
    
    def _run_single_farm_cycle(self, farm, commander_id):
        """
        Egyetlen farm ciklus futtatása (base_farm logika használata)
        
        Args:
            farm: BaseFarm instance
            commander_id: Commander ID
            
        Returns:
            dict: {'march_time': X, 'gather_time': Y} vagy "RESTART"
        """
        log.separator('-', 60)
        log.info(f"Farm folyamat indítása: {farm.farm_type.upper()}")
        log.separator('-', 60)
        
        try:
            # Base farm logikát használjuk, de NEM loop
            # Egyetlen futás:
            
            # 1. SPACE
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("SPACE billentyű")
            press_key('space')
            
            # 2. B (térkép)
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("B billentyű (térkép)")
            press_key('b')
            
            # 3. Resource icon
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('resource_icon', [0, 0])
            log.click(f"{farm.farm_type.upper()} ikon → {coords}")
            safe_click(coords)
            
            # 4. Level button
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('level_button', [0, 0])
            log.click(f"Szint gomb → {coords}")
            safe_click(coords)
            
            # 5. Search button
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('search_button', [0, 0])
            log.click(f"Keresés gomb → {coords}")
            safe_click(coords)
            
            # 6. Gather button (template match)
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            gather_coords = farm.find_gather_button()
            
            if not gather_coords:
                log.error("Gather gomb nem található!")
                press_key('space')
                return "RESTART"
            
            log.success(f"Gather gomb → {gather_coords}")
            safe_click(gather_coords)
            
            # 7. New troops
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('new_troops', [0, 0])
            log.click(f"New troops → {coords}")
            safe_click(coords)
            
            # 8. March Time OCR
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            march_time = farm.read_time('march_time')
            
            if march_time is None:
                march_time = self.default_march_time
                log.warning(f"March Time OCR hiba! Default: {march_time} sec")
            else:
                log.success(f"March Time: {format_time(march_time)} ({march_time} sec)")
            
            # 9. March button
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('march_button', [0, 0])
            log.click(f"March gomb → {coords}")
            safe_click(coords)
            
            # 10. Várakozás (march + 1 sec)
            wait_duration = march_time + 1
            log.wait(f"Várakozás {wait_duration} sec (march + 1)")
            time.sleep(wait_duration)
            
            # 11. Képernyő közepe
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            screen_center = get_screen_center()
            coords = farm.coords.get('screen_center', screen_center)
            log.click(f"Képernyő közép → {coords}")
            safe_click(coords)
            
            # 12. Gather Time OCR (retry 30x)
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            gather_time = None
            for attempt in range(30):
                gather_time = farm.read_time('gather_time')
                if gather_time is not None:
                    log.success(f"Gather Time: {format_time(gather_time)} ({gather_time} sec) - {attempt+1}. próba")
                    break
                log.warning(f"Gather Time OCR hiba ({attempt+1}/30), retry...")
                time.sleep(0.5)
            
            if gather_time is None:
                gather_time = self.default_gather_time
                log.warning(f"Gather Time OCR véglegesen sikertelen! Default: {gather_time} sec")
            
            # 13. SPACE (bezárás)
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("SPACE (bezárás)")
            press_key('space')
            
            log.separator('-', 60)
            log.success(f"Farm ciklus befejezve: March={format_time(march_time)}, Gather={format_time(gather_time)}")
            log.separator('-', 60)
            
            return {
                'march_time': march_time,
                'gather_time': gather_time
            }
        
        except Exception as e:
            log.error(f"Farm ciklus hiba: {e}")
            import traceback
            traceback.print_exc()
            return "RESTART"


# Globális singleton instance
gathering_manager = GatheringManager()


# ===== TESZT =====
if __name__ == "__main__":
    log.separator('=', 60)
    log.info("GATHERING MANAGER TESZT")
    log.separator('=', 60)
    
    # Initial start
    gathering_manager.initial_start_all_commanders()
    
    # Commander run (mock)
    # result = gathering_manager.run_commander(1)
    # print(f"Result: {result}")
    
    log.separator('=', 60)
    log.info("TESZT VÉGE")
    log.separator('=', 60)