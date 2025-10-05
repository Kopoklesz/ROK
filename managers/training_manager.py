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
        
        log.info("[Training] Manager inicializálva")
    
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
            
            # OCR
            remaining_time = self._read_building_time(building_name)
            
            if remaining_time is None:
                log.warning(f"[Training] {building_name.upper()}: OCR sikertelen, skip")
                continue
            
            log.success(f"[Training] {building_name.upper()}: {format_time(remaining_time)} van hátra ({remaining_time} sec)")
            
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
            log.warning(f"[Training] {building_name.upper()} time region nincs beállítva!")
            return None
        
        log.ocr(f"[Training] {building_name.upper()} time OCR → Region: (x:{region.get('x',0)}, y:{region.get('y',0)}, w:{region.get('width',0)}, h:{region.get('height',0)})")
        
        ocr_text = ImageManager.read_text_from_region(region)
        
        if not ocr_text:
            log.warning(f"[Training] {building_name.upper()} OCR üres eredmény")
            return None
        
        log.info(f"[Training] {building_name.upper()} OCR nyers szöveg: '{ocr_text}'")
        
        time_sec = parse_time(ocr_text)
        
        if time_sec is None:
            log.warning(f"[Training] {building_name.upper()} OCR parse hiba: '{ocr_text}'")
        else:
            log.success(f"[Training] {building_name.upper()} parsed time: {time_sec} sec")
        
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
            task_data: Task extra adat {'building': 'barracks'}
        """
        building = task_data.get('building', 'barracks')
        
        log.separator('=', 60)
        log.info(f"[Training] ⚔️  {building.upper()} TRAINING RESTART")
        log.separator('=', 60)
        
        building_config = self.buildings.get(building, {})
        
        if not building_config.get('enabled', False):
            log.warning(f"[Training] {building.upper()} disabled, restart skip")
            return
        
        log.info(f"[Training] {building.upper()} koordináták betöltése...")
        building_coords = self.coords.get(building, {})
        
        # Koordináták kiolvasása
        troop_gather_coords = building_coords.get('troop_gather', [0, 0])
        building_coords_val = building_coords.get('building', [0, 0])
        button_coords = building_coords.get('button', [0, 0])
        tier_coords = building_coords.get('tier', [0, 0])
        confirm_coords = building_coords.get('confirm', [0, 0])
        
        log.info(f"[Training] Koordináták:")
        log.info(f"  troop_gather: {troop_gather_coords}")
        log.info(f"  building: {building_coords_val}")
        log.info(f"  button: {button_coords}")
        log.info(f"  tier: {tier_coords}")
        log.info(f"  confirm: {confirm_coords}")
        
        # ===== 1. TROOP GATHER =====
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"[Training] Várakozás {delay:.1f} mp")
        time.sleep(delay)
        
        log.click(f"[Training] TROOP GATHER kattintás → {troop_gather_coords}")
        safe_click(troop_gather_coords)
        log.success(f"[Training] TROOP GATHER OK")
        
        # ===== 2. BUILDING =====
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"[Training] Várakozás {delay:.1f} mp")
        time.sleep(delay)
        
        log.click(f"[Training] BUILDING kattintás → {building_coords_val}")
        safe_click(building_coords_val)
        log.success(f"[Training] BUILDING OK")
        
        # ===== 3. BUTTON =====
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"[Training] Várakozás {delay:.1f} mp")
        time.sleep(delay)
        
        log.click(f"[Training] BUTTON kattintás → {button_coords}")
        safe_click(button_coords)
        log.success(f"[Training] BUTTON OK")
        
        # ===== 4. TIER =====
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"[Training] Várakozás {delay:.1f} mp")
        time.sleep(delay)
        
        log.click(f"[Training] TIER kattintás → {tier_coords}")
        safe_click(tier_coords)
        log.success(f"[Training] TIER OK")
        
        # ===== 5. CONFIRM =====
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"[Training] Várakozás {delay:.1f} mp")
        time.sleep(delay)
        
        log.click(f"[Training] CONFIRM kattintás → {confirm_coords}")
        safe_click(confirm_coords)
        log.success(f"[Training] CONFIRM OK")
        
        # ===== 6. SPACE #1 =====
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"[Training] Várakozás {delay:.1f} mp")
        time.sleep(delay)
        
        log.action("[Training] SPACE #1 lenyomása")
        press_key('space')
        log.success(f"[Training] SPACE #1 OK")
        
        # ===== 7. SPACE #2 =====
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"[Training] Várakozás {delay:.1f} mp")
        time.sleep(delay)
        
        log.action("[Training] SPACE #2 lenyomása")
        press_key('space')
        log.success(f"[Training] SPACE #2 OK")
        
        # ===== 8. ÚJ OCR + Timer =====
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"[Training] Várakozás {delay:.1f} mp (OCR előtt)")
        time.sleep(delay)
        
        log.info(f"[Training] {building.upper()} új training time OCR...")
        new_time = self._read_building_time(building)
        
        if new_time is None:
            # Default fallback
            new_time = 3600  # 1 óra
            log.warning(f"[Training] {building.upper()} OCR sikertelen, default: 1 óra ({new_time} sec)")
        else:
            log.success(f"[Training] {building.upper()} új idő: {format_time(new_time)} ({new_time} sec)")
        
        # Új timer beállítás
        self._set_building_timer(building, new_time, building_config)
        
        log.separator('=', 60)
        log.success(f"[Training] {building.upper()} training restart befejezve")
        log.separator('=', 60)


# Globális singleton instance
training_manager = TrainingManager()