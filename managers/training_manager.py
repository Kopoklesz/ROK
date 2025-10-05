"""
Auto Farm - Training Manager
Training buildings OCR-based időzítés
"""
import json
import time
import threading
from pathlib import Path

from library import ImageManager, safe_click, press_key, wait_random
from utils.logger import FarmLogger as log
from utils.time_utils import parse_time, format_time
from utils.timer_manager import timer_manager
from utils.queue_manager import queue_manager


class TrainingManager:
    """Training manager OCR időzítéssel"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / 'config'
        
        # Config betöltés
        self.settings = self._load_settings()
        self.time_regions = self._load_time_regions()
        self.coords = self._load_coords()
        
        # Buildings config
        self.buildings = self.settings.get('training', {}).get('buildings', {})
        
        # Thread control
        self.running = False
        self.thread = None
        
        # Human wait
        human_wait = self.settings.get('human_wait', {})
        self.human_wait_min = human_wait.get('min_seconds', 5)
        self.human_wait_max = human_wait.get('max_seconds', 10)
    
    def _load_settings(self):
        """Settings.json betöltése"""
        settings_file = self.config_dir / 'settings.json'
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_time_regions(self):
        """Training time regions betöltése"""
        regions_file = self.config_dir / 'training_time_regions.json'
        if regions_file.exists():
            with open(regions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_coords(self):
        """Training coords betöltése"""
        coords_file = self.config_dir / 'training_coords.json'
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def start(self):
        """
        Training Manager indítás
        
        Induláskor:
        1. Összes enabled building OCR
        2. Timer beállítás
        """
        if self.running:
            log.warning("Training Manager már fut!")
            return
        
        log.separator('=', 60)
        log.info("Training Manager indítás...")
        log.separator('=', 60)
        
        # Első OCR check (induláskor)
        self._initial_ocr_all_buildings()
        
        log.separator('=', 60)
        log.success("Training Manager inicializálva")
        log.separator('=', 60)
    
    def stop(self):
        """Training Manager leállítás"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        
        log.info("Training Manager leállítva")
    
    def _initial_ocr_all_buildings(self):
        """
        Induláskor összes enabled building OCR + timer
        """
        for building_name, building_config in self.buildings.items():
            enabled = building_config.get('enabled', False)
            
            if not enabled:
                log.info(f"{building_name.upper()}: Disabled, skip")
                continue
            
            log.info(f"{building_name.upper()}: OCR check...")
            
            # OCR
            remaining_time = self._read_building_time(building_name)
            
            if remaining_time is None:
                log.warning(f"{building_name.upper()}: OCR sikertelen, skip")
                continue
            
            log.success(f"{building_name.upper()}: {format_time(remaining_time)} van hátra")
            
            # Timer beállítás
            self._set_building_timer(building_name, remaining_time, building_config)
    
    def _read_building_time(self, building_name):
        """
        Building training time OCR
        
        Args:
            building_name: 'barracks', 'archery', 'stable', 'siege'
            
        Returns:
            int: Másodpercek vagy None
        """
        region_key = f"{building_name}_time"
        region = self.time_regions.get(region_key)
        
        if not region:
            log.warning(f"{building_name.upper()} time region nincs beállítva!")
            return None
        
        ocr_text = ImageManager.read_text_from_region(region)
        
        if not ocr_text:
            return None
        
        time_sec = parse_time(ocr_text)
        
        if time_sec is None:
            log.warning(f"{building_name.upper()} OCR parse hiba: '{ocr_text}'")
        
        return time_sec
    
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
        
        if remaining_time <= prep_time:
            # Azonnal timer
            timer_manager.add_timer(
                timer_id=timer_id,
                deadline_seconds=remaining_time,
                task_id=task_id,
                task_type="training",
                data={"building": building_name}
            )
            log.success(f"{building_name.upper()} timer: {format_time(remaining_time)} múlva restart")
        else:
            # Teljes idő timer (restart után újra OCR)
            timer_manager.add_timer(
                timer_id=timer_id,
                deadline_seconds=remaining_time,
                task_id=task_id,
                task_type="training",
                data={"building": building_name}
            )
            log.success(f"{building_name.upper()} timer: {format_time(remaining_time)} múlva restart")
    
    def restart_training(self, task_data):
        """
        Training restart folyamat
        
        Args:
            task_data: Task extra adat {'building': 'barracks'}
        """
        building = task_data.get('building', 'barracks')
        
        log.separator('=', 60)
        log.info(f"⚔️  {building.upper()} TRAINING RESTART")
        log.separator('=', 60)
        
        building_config = self.buildings.get(building, {})
        
        if not building_config.get('enabled', False):
            log.warning(f"{building.upper()} disabled, restart skip")
            return
        
        # 1. SPACE (city view)
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        log.action("SPACE (city view)")
        press_key('space')
        
        # 2. Building icon kattintás
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        
        building_coords = self.coords.get(building, {})
        icon_coords = building_coords.get('building_icon', [0, 0])
        log.click(f"{building.upper()} ikon → {icon_coords}")
        safe_click(icon_coords)
        
        # TODO: Troop type selection (tier logic)
        log.info("TODO: Troop type selection (tier1, tier2, tier3 mix)")
        
        # 3. Max button
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        
        max_coords = building_coords.get('max_button', [0, 0])
        log.click(f"Max button → {max_coords}")
        safe_click(max_coords)
        
        # 4. Train button
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        
        train_coords = building_coords.get('train_button', [0, 0])
        log.click(f"Train button → {train_coords}")
        safe_click(train_coords)
        
        # 5. SPACE (bezárás)
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        log.action("SPACE (bezárás)")
        press_key('space')
        
        # 6. ÚJ OCR + Timer
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp (OCR előtt)")
        time.sleep(delay)
        
        log.info(f"{building.upper()} új training time OCR...")
        new_time = self._read_building_time(building)
        
        if new_time is None:
            # Default fallback
            new_time = 3600  # 1 óra
            log.warning(f"{building.upper()} OCR sikertelen, default: 1 óra")
        else:
            log.success(f"{building.upper()} új idő: {format_time(new_time)}")
        
        # Új timer beállítás
        self._set_building_timer(building, new_time, building_config)
        
        log.separator('=', 60)
        log.success(f"{building.upper()} training restart befejezve")
        log.separator('=', 60)


# Globális singleton instance
training_manager = TrainingManager()