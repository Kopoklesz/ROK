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
        
        log.info("[Gathering] Manager inicializálása...")
        
        # Config betöltés
        self.settings = self._load_settings()
        self.farm_regions = self._load_farm_regions()
        
        # Commander config
        self.max_commanders = self.settings.get('gathering', {}).get('max_commanders', 4)
        self.commanders = self.settings.get('gathering', {}).get('commanders', [])
        
        log.info(f"[Gathering] Max commanders: {self.max_commanders}")
        log.info(f"[Gathering] Configured commanders: {len(self.commanders)}")
        
        # Human wait
        human_wait = self.settings.get('human_wait', {})
        self.human_wait_min = human_wait.get('min_seconds', 5)
        self.human_wait_max = human_wait.get('max_seconds', 10)
        
        log.info(f"[Gathering] Human wait: {self.human_wait_min}-{self.human_wait_max} sec")
        
        # Defaults
        defaults = self.settings.get('defaults', {})
        self.default_march_time = defaults.get('march_time_seconds', 300)
        self.default_gather_time = defaults.get('gather_time_seconds', 5400)
        
        log.info(f"[Gathering] Default march time: {self.default_march_time} sec")
        log.info(f"[Gathering] Default gather time: {self.default_gather_time} sec")
        
        # Base farm instance-ok (resource típusonként)
        self.farms = {
            'wheat': BaseFarm('wheat', self.config_dir),
            'wood': BaseFarm('wood', self.config_dir),
            'stone': BaseFarm('stone', self.config_dir),
            'gold': BaseFarm('gold', self.config_dir)
        }
        
        log.success("[Gathering] Manager inicializálva")
    
    def _load_settings(self):
        """Settings.json betöltése"""
        settings_file = self.config_dir / 'settings.json'
        log.info(f"[Gathering] Settings betöltése: {settings_file}")
        
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                log.success(f"[Gathering] Settings betöltve")
                return settings
        
        log.warning(f"[Gathering] Settings nem található, üres dict")
        return {}
    
    def _load_farm_regions(self):
        """Farm regions betöltése"""
        regions_file = self.config_dir / 'farm_regions.json'
        log.info(f"[Gathering] Farm regions betöltése: {regions_file}")
        
        if regions_file.exists():
            with open(regions_file, 'r', encoding='utf-8') as f:
                regions = json.load(f)
                log.success(f"[Gathering] Farm regions betöltve: {len(regions)} resource")
                return regions
        
        log.warning(f"[Gathering] Farm regions nem található, üres dict")
        return {}
    
    def initial_start_all_commanders(self):
        """
        Első indulás: összes enabled commander queue-ba
        """
        log.separator('=', 60)
        log.info("[Gathering] 🌾 COMMANDERS ELSŐ INDÍTÁSA")
        log.separator('=', 60)
        
        enabled_count = 0
        disabled_count = 0
        
        for commander in self.commanders:
            commander_id = commander.get('id')
            enabled = commander.get('enabled', True)
            
            if enabled:
                task_id = f"commander_{commander_id}_start"
                log.info(f"[Gathering] Commander #{commander_id} queue-ba helyezése...")
                queue_manager.add_task(task_id, "gathering", {"commander_id": commander_id})
                log.success(f"[Gathering] Commander #{commander_id} queue-ba téve (start)")
                enabled_count += 1
            else:
                log.info(f"[Gathering] Commander #{commander_id} disabled, skip")
                disabled_count += 1
        
        log.separator('-', 60)
        log.success(f"[Gathering] {enabled_count} commander queue-ba téve, {disabled_count} disabled")
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
        log.info(f"[Gathering] 🌾 COMMANDER #{commander_id} - GATHERING START")
        log.separator('=', 60)
        
        log.info(f"[Gathering] Commander #{commander_id} indítása...")
        
        # 1. Resource OCR
        log.info(f"[Gathering] Step 1/5: Resource OCR")
        resources = self._read_all_resources()
        
        if not resources:
            log.error("[Gathering] Nincs beállított erőforrás régió!")
            log.error(f"[Gathering] Commander #{commander_id} RESTART szükséges")
            return "RESTART"
        
        log.success(f"[Gathering] {len(resources)} resource OCR OK")
        
        # 2. Minimum resource kiválasztás
        log.info(f"[Gathering] Step 2/5: Minimum resource kiválasztás")
        selected_resource = self._select_minimum_resource(resources)
        
        log.success(f"[Gathering] Commander #{commander_id} → {selected_resource.upper()} farmolás")
        
        # 3. Farm instance
        log.info(f"[Gathering] Step 3/5: Farm instance betöltése")
        farm = self.farms.get(selected_resource)
        
        if not farm:
            log.error(f"[Gathering] Farm instance nem található: {selected_resource}")
            log.error(f"[Gathering] Commander #{commander_id} RESTART szükséges")
            return "RESTART"
        
        log.success(f"[Gathering] Farm instance OK: {selected_resource}")
        
        # 4. Farm process futtatása
        log.info(f"[Gathering] Step 4/5: Farm process futtatása")
        result = self._run_single_farm_cycle(farm, commander_id)
        
        if result == "RESTART":
            log.error(f"[Gathering] Farm process sikertelen")
            log.warning(f"[Gathering] Commander #{commander_id} RESTART szükséges!")
            return "RESTART"
        
        log.success(f"[Gathering] Farm process OK")
        
        # 5. Timer beállítása
        log.info(f"[Gathering] Step 5/5: Timer beállítása")
        march_time = result.get('march_time', self.default_march_time)
        gather_time = result.get('gather_time', self.default_gather_time)
        total_time = march_time + gather_time
        
        log.info(f"[Gathering] Commander #{commander_id} - March time: {format_time(march_time)} ({march_time} sec)")
        log.info(f"[Gathering] Commander #{commander_id} - Gather time: {format_time(gather_time)} ({gather_time} sec)")
        log.info(f"[Gathering] Commander #{commander_id} - Össz idő: {format_time(total_time)} ({total_time} sec)")
        
        # Timer hozzáadás
        timer_id = f"commander_{commander_id}"
        task_id = f"commander_{commander_id}_restart"
        
        log.info(f"[Gathering] Timer beállítása: {timer_id}")
        log.info(f"[Gathering]   Deadline: {total_time} sec múlva")
        log.info(f"[Gathering]   Callback task: {task_id}")
        
        timer_manager.add_timer(
            timer_id=timer_id,
            deadline_seconds=total_time,
            task_id=task_id,
            task_type="gathering",
            data={"commander_id": commander_id}
        )
        
        log.success(f"[Gathering] Commander #{commander_id} timer beállítva: {format_time(total_time)} múlva restart")
        
        log.separator('=', 60)
        log.success(f"[Gathering] Commander #{commander_id} SIKERES BEFEJEZÉS")
        log.separator('=', 60)
        
        return "SUCCESS"
    
    def _read_all_resources(self):
        """Összes erőforrás OCR kiolvasása"""
        log.separator('-', 60)
        log.info("[Gathering] 📊 ERŐFORRÁSOK KIOLVASÁSA")
        log.separator('-', 60)
        
        resources = {}
        success_count = 0
        skip_count = 0
        
        for resource_name, region in self.farm_regions.items():
            if region is None:
                log.info(f"[Gathering] {resource_name.upper()}: Region nincs beállítva, skip")
                skip_count += 1
                continue
            
            log.ocr(f"[Gathering] {resource_name.upper()} OCR → Region: (x:{region.get('x',0)}, y:{region.get('y',0)}, w:{region.get('width',0)}, h:{region.get('height',0)})")
            
            ocr_text = ImageManager.read_text_from_region(region)
            log.info(f"[Gathering] {resource_name.upper()} OCR nyers: '{ocr_text}'")
            
            value = parse_resource_value(ocr_text)
            resources[resource_name] = value
            
            log.success(f"[Gathering] {resource_name.upper()}: {ocr_text} → {value:,}")
            success_count += 1
        
        log.separator('-', 60)
        log.success(f"[Gathering] OCR befejezve: {success_count} resource OK, {skip_count} skip")
        log.separator('-', 60)
        
        return resources
    
    def _select_minimum_resource(self, resources):
        """Legkisebb erőforrás kiválasztása (osztással)"""
        log.separator('-', 60)
        log.info("[Gathering] 🧮 ERŐFORRÁS ÉRTÉKELÉS")
        log.separator('-', 60)
        
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
            log.info(f"[Gathering]   {res.upper()}: {amount:,} ÷ {divisor} = {values[res]:,.1f}")
        
        min_resource = min(values, key=values.get)
        
        log.separator('-', 60)
        log.success(f"[Gathering]   MINIMUM: {min_resource.upper()} ({values[min_resource]:,.1f})")
        log.separator('-', 60)
        
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
        log.info(f"[Gathering] 🚜 FARM FOLYAMAT: {farm.farm_type.upper()}")
        log.separator('-', 60)
        
        try:
            # 1. SPACE
            log.info(f"[Gathering] [1/13] SPACE billentyű")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("[Gathering] SPACE lenyomása")
            press_key('space')
            log.success(f"[Gathering] SPACE OK")
            
            # 2. B (térkép)
            log.info(f"[Gathering] [2/13] B billentyű (térkép)")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("[Gathering] B billentyű lenyomása")
            press_key('b')
            log.success(f"[Gathering] B OK")
            
            # 3. Resource icon
            log.info(f"[Gathering] [3/13] Resource icon kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('resource_icon', [0, 0])
            log.click(f"[Gathering] {farm.farm_type.upper()} ikon → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] Resource icon OK")
            
            # 4. Level button
            log.info(f"[Gathering] [4/13] Level button kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('level_button', [0, 0])
            log.click(f"[Gathering] Szint gomb → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] Level button OK")
            
            # 5. Search button
            log.info(f"[Gathering] [5/13] Search button kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('search_button', [0, 0])
            log.click(f"[Gathering] Keresés gomb → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] Search button OK")
            
            # 6. Gather button (template match)
            log.info(f"[Gathering] [6/13] Gather button keresés")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            log.search(f"[Gathering] gather.png keresés...")
            gather_coords = farm.find_gather_button()
            
            if not gather_coords:
                log.error("[Gathering] Gather gomb nem található!")
                log.action("[Gathering] SPACE lenyomása (bezárás)")
                press_key('space')
                return "RESTART"
            
            log.success(f"[Gathering] Gather gomb megtalálva → {gather_coords}")
            log.click(f"[Gathering] Gather gomb kattintás")
            safe_click(gather_coords)
            log.success(f"[Gathering] Gather button OK")
            
            # 7. New troops
            log.info(f"[Gathering] [7/13] New troops kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('new_troops', [0, 0])
            log.click(f"[Gathering] New troops → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] New troops OK")
            
            # 8. March Time OCR
            log.info(f"[Gathering] [8/13] March Time OCR")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            log.ocr(f"[Gathering] March Time kiolvasása...")
            march_time = farm.read_time('march_time')
            
            if march_time is None:
                march_time = self.default_march_time
                log.warning(f"[Gathering] March Time OCR hiba! Default: {march_time} sec")
            else:
                log.success(f"[Gathering] March Time: {format_time(march_time)} ({march_time} sec)")
            
            # 9. March button
            log.info(f"[Gathering] [9/13] March button kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('march_button', [0, 0])
            log.click(f"[Gathering] March gomb → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] March button OK")
            
            # 10. Várakozás (march + 1 sec)
            log.info(f"[Gathering] [10/13] Várakozás march time + 1 sec")
            wait_duration = march_time + 1
            log.wait(f"[Gathering] Várakozás {wait_duration} sec (march time + 1)")
            time.sleep(wait_duration)
            log.success(f"[Gathering] Várakozás OK")
            
            # 11. Képernyő közepe
            log.info(f"[Gathering] [11/13] Képernyő közép kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            screen_center = get_screen_center()
            coords = farm.coords.get('screen_center', screen_center)
            log.click(f"[Gathering] Képernyő közép → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] Screen center OK")
            
            # 12. Gather Time OCR (retry 60x, 1.0 sec)
            log.info(f"[Gathering] [12/13] Gather Time OCR (max 60 retry)")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            gather_time = None
            for attempt in range(60):
                log.ocr(f"[Gathering] Gather Time kiolvasás (kísérlet {attempt+1}/60)...")
                gather_time = farm.read_time('gather_time')
                
                if gather_time is not None:
                    log.success(f"[Gathering] Gather Time: {format_time(gather_time)} ({gather_time} sec) - {attempt+1}. próba")
                    break
                
                if (attempt + 1) % 10 == 0:
                    log.warning(f"[Gathering] Gather Time OCR hiba ({attempt+1}/60), retry...")
                
                time.sleep(1.0)
            
            if gather_time is None:
                gather_time = self.default_gather_time
                log.error(f"[Gathering] Gather Time OCR véglegesen sikertelen!")
                log.warning(f"[Gathering] Default érték használata: {gather_time} sec")
            
            # 13. SPACE (bezárás)
            log.info(f"[Gathering] [13/13] SPACE (bezárás)")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("[Gathering] SPACE lenyomása")
            press_key('space')
            log.success(f"[Gathering] SPACE OK")
            
            log.separator('-', 60)
            log.success(f"[Gathering] Farm ciklus befejezve: March={format_time(march_time)}, Gather={format_time(gather_time)}")
            log.separator('-', 60)
            
            return {
                'march_time': march_time,
                'gather_time': gather_time
            }
        
        except Exception as e:
            log.error(f"[Gathering] Farm ciklus HIBA: {e}")
            import traceback
            traceback.print_exc()
            return "RESTART"


# Globális singleton instance
gathering_manager = GatheringManager()