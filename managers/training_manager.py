"""
ROK Auto Farm - Training Manager
JAVÍTOTT VERZIÓ:
- OCR validáció max időkkel (infantry: 12h, archer: 8h, cavalry: 15h, ram: 1h)
- 10 próba után fail → 5 perc retry
"""
import time
import json
import threading
from pathlib import Path

from library import safe_click, press_key, wait_random
from utils.logger import FarmLogger as log
from utils.queue_manager import queue_manager
from utils.timer_manager import timer_manager
from utils.time_utils import parse_time, format_time
from library import ImageManager


class TrainingManager:
    """Training Manager - Katonák kiképzése"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / 'config'
        
        # Settings betöltése
        settings_file = self.config_dir / 'settings.json'
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Training config
        training_config = settings.get('training', {})
        self.buildings = training_config.get('buildings', {})
        
        # Human wait
        human_wait = settings.get('human_wait', {})
        self.human_wait_min = human_wait.get('min_seconds', 5)
        self.human_wait_max = human_wait.get('max_seconds', 10)
        
        # Training time régiók
        time_regions_file = self.config_dir / 'training_time_regions.json'
        if time_regions_file.exists():
            with open(time_regions_file, 'r', encoding='utf-8') as f:
                self.time_regions = json.load(f)
        else:
            self.time_regions = {}
        
        # Training koordináták
        training_coords_file = self.config_dir / 'training_coords.json'
        if training_coords_file.exists():
            with open(training_coords_file, 'r', encoding='utf-8') as f:
                self.training_coords = json.load(f)
        else:
            self.training_coords = {}
        
        self.running = False
        self.thread = None
    
    def start(self):
        """
        Training Manager indítás
        
        1. Összes enabled building OCR
        2. Timer beállítás
        """
        if self.running:
            log.warning("[Training] Manager már fut!")
            return
        
        log.separator('=', 60)
        log.info("[Training] Manager indítás...")
        log.separator('=', 60)
        
        # Első OCR check (induláskor)
        self._initial_ocr_all_buildings()
        
        log.separator('=', 60)
        log.success("[Training] Manager inicializálva")
        log.separator('=', 60)
        
        self.running = True
    
    def stop(self):
        """Training Manager leállítás"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        
        log.info("[Training] Manager leállítva")
    
    def _initial_ocr_all_buildings(self):
        """
        Induláskor összes enabled building OCR + timer
        """
        log.info("[Training] Kezdeti OCR check minden enabled building-re")
        
        for building_name, building_config in self.buildings.items():
            enabled = building_config.get('enabled', False)
            
            if not enabled:
                log.info(f"[Training] {building_name.upper()}: Disabled, skip")
                continue
            
            log.info(f"[Training] {building_name.upper()}: OCR check indítása...")
            
            # OCR + VALIDÁCIÓ
            remaining_time = self._read_building_time_with_validation(building_name)
            
            if remaining_time is None:
                log.warning(f"[Training] {building_name.upper()}: OCR sikertelen")
                log.info(f"[Training] {building_name.upper()}: 5 perc múlva újra próbálkozás")
                
                # 5 perc retry
                timer_manager.add_timer(
                    timer_id=f"training_{building_name}_retry",
                    deadline_seconds=300,
                    task_id=f"{building_name}_ocr_retry",
                    task_type="training",
                    data={"building": building_name}
                )
                continue
            
            log.success(f"[Training] {building_name.upper()}: {format_time(remaining_time)} van hátra ({remaining_time} sec)")
            
            # Timer beállítás
            self._set_building_timer(building_name, remaining_time, building_config)
    
    def _read_building_time_with_validation(self, building_name, max_attempts=10):
        """
        Building time OCR + validáció
        
        Max időkorlátok:
        - barracks (infantry): 12h (43200 sec)
        - archery (archer): 8h (28800 sec)
        - stable (cavalry): 15h (54000 sec)
        - siege (ram): 1h (3600 sec)
        
        Args:
            building_name: 'barracks', 'archery', 'stable', 'siege'
            max_attempts: Max próbálkozások száma (default: 10)
            
        Returns:
            int: Másodpercek vagy None
        """
        max_times = {
            'barracks': 43200,   # 12h infantry
            'archery': 28800,    # 8h archer
            'stable': 54000,     # 15h cavalry
            'siege': 3600        # 1h ram
        }
        
        max_time = max_times.get(building_name, 86400)  # default 24h
        region_key = f"{building_name}_time"
        region = self.time_regions.get(region_key)
        
        if not region:
            log.warning(f"[Training] {building_name.upper()} time region nincs beállítva!")
            return None
        
        log.ocr(f"[Training] {building_name.upper()} time OCR → Region: (x:{region.get('x',0)}, y:{region.get('y',0)}, w:{region.get('width',0)}, h:{region.get('height',0)})")
        
        for attempt in range(1, max_attempts + 1):
            ocr_text = ImageManager.read_text_from_region(region)
            
            if not ocr_text:
                time.sleep(1.0)
                continue
            
            log.info(f"[Training] {building_name.upper()} OCR nyers szöveg (kísérlet {attempt}): '{ocr_text}'")
            
            time_sec = parse_time(ocr_text)
            
            if time_sec and time_sec <= max_time:
                log.success(f"[Training] {building_name.upper()} parsed time: {time_sec} sec ({format_time(time_sec)}) - {attempt}. próba")
                return time_sec
            elif time_sec and time_sec > max_time:
                log.warning(f"[Training] {building_name.upper()} túl nagy idő: {format_time(time_sec)} > {format_time(max_time)}, retry...")
            
            time.sleep(1.0)
        
        log.error(f"[Training] {building_name.upper()} OCR sikertelen {max_attempts} próba után!")
        return None
    
    def _set_building_timer(self, building_name, remaining_time, building_config):
        """
        Timer beállítása building-hez
        
        Args:
            building_name: Building név
            remaining_time: Hátralevő idő (sec)
            building_config: Building config dict
        """
        prep_time = building_config.get('prep_time_seconds', 300)
        
        timer_id = f"training_{building_name}"
        task_id = f"{building_name}_restart"
        
        log.info(f"[Training] {building_name.upper()} timer beállítása...")
        log.info(f"[Training] Remaining time: {remaining_time} sec, Prep time: {prep_time} sec")
        
        if remaining_time <= prep_time:
            # Azonnal timer
            timer_manager.add_timer(
                timer_id=timer_id,
                deadline_seconds=remaining_time,
                task_id=task_id,
                task_type="training",
                data={"building": building_name}
            )
            log.success(f"[Training] {building_name.upper()} timer: {format_time(remaining_time)} múlva restart")
        else:
            # Teljes idő timer (restart után újra OCR)
            timer_manager.add_timer(
                timer_id=timer_id,
                deadline_seconds=remaining_time,
                task_id=task_id,
                task_type="training",
                data={"building": building_name}
            )
            log.success(f"[Training] {building_name.upper()} timer: {format_time(remaining_time)} múlva restart")
    
    def restart_training(self, task_data):
        """
        Training restart folyamat
        
        5 FIX KOORDINÁTA:
        1. troop_gather (UGYANAZ mint building)
        2. building
        3. button
        4. tier
        5. confirm
        + 2x SPACE
        
        Args:
            task_data: {'building': 'barracks'}
        """
        building_name = task_data.get('building', 'barracks')
        
        log.separator('=', 60)
        log.info(f"[Training] ⚔️  {building_name.upper()} TRAINING RESTART")
        log.separator('=', 60)
        
        # Koordináták betöltése
        coords = self.training_coords.get(building_name, {})
        
        log.info(f"[Training] {building_name.upper()} koordináták betöltése...")
        log.info(f"[Training] Koordináták:")
        log.info(f"   troop_gather: {coords.get('troop_gather', [0,0])}")
        log.info(f"   building: {coords.get('building', [0,0])}")
        log.info(f"   button: {coords.get('button', [0,0])}")
        log.info(f"   tier: {coords.get('tier', [0,0])}")
        log.info(f"   confirm: {coords.get('confirm', [0,0])}")
        
        try:
            # 1. Troop Gather
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            troop_gather_coords = coords.get('troop_gather', [0, 0])
            log.click(f"[Training] TROOP GATHER kattintás → {troop_gather_coords}")
            safe_click(troop_gather_coords)
            log.success("[Training] TROOP GATHER OK")
            
            # 2. Building
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            building_coords = coords.get('building', [0, 0])
            log.click(f"[Training] BUILDING kattintás → {building_coords}")
            safe_click(building_coords)
            log.success("[Training] BUILDING OK")
            
            # 3. Button
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            button_coords = coords.get('button', [0, 0])
            log.click(f"[Training] BUTTON kattintás → {button_coords}")
            safe_click(button_coords)
            log.success("[Training] BUTTON OK")
            
            # 4. Tier
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            tier_coords = coords.get('tier', [0, 0])
            log.click(f"[Training] TIER kattintás → {tier_coords}")
            safe_click(tier_coords)
            log.success("[Training] TIER OK")
            
            # 5. Confirm
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            confirm_coords = coords.get('confirm', [0, 0])
            log.click(f"[Training] CONFIRM kattintás → {confirm_coords}")
            safe_click(confirm_coords)
            log.success("[Training] CONFIRM OK")
            
            # 6. SPACE #1
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("[Training] SPACE #1 lenyomása")
            press_key('space')
            log.success("[Training] SPACE #1 OK")
            
            # 7. SPACE #2
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("[Training] SPACE #2 lenyomása")
            press_key('space')
            log.success("[Training] SPACE #2 OK")
            
            # 8. Várakozás OCR előtt
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp (OCR előtt)")
            time.sleep(delay)
            
            # 9. Új training time OCR + validáció
            log.info(f"[Training] {building_name.upper()} új training time OCR...")
            
            new_time = self._read_building_time_with_validation(building_name)
            
            if new_time is None:
                log.error(f"[Training] {building_name.upper()} OCR sikertelen restart után!")
                log.info(f"[Training] {building_name.upper()}: 5 perc múlva újra próbálkozás")
                
                # 5 perc retry
                timer_manager.add_timer(
                    timer_id=f"training_{building_name}_retry",
                    deadline_seconds=300,
                    task_id=f"{building_name}_restart",
                    task_type="training",
                    data={"building": building_name}
                )
                
                log.separator('=', 60)
                log.warning(f"[Training] {building_name.upper()} training restart sikertelen (OCR fail)")
                log.separator('=', 60)
                return
            
            log.success(f"[Training] {building_name.upper()} új idő: {format_time(new_time)} ({new_time} sec)")
            
            # Timer beállítás
            building_config = self.buildings.get(building_name, {})
            self._set_building_timer(building_name, new_time, building_config)
            
            log.separator('=', 60)
            log.success(f"[Training] {building_name.upper()} training restart befejezve")
            log.separator('=', 60)
        
        except Exception as e:
            log.error(f"[Training] {building_name.upper()} restart HIBA: {e}")
            import traceback
            traceback.print_exc()


# Globális singleton instance
training_manager = TrainingManager()