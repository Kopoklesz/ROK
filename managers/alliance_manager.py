"""
Auto Farm - Alliance Manager
Alliance help 5 perces timer-rel
MÓDOSÍTVA: 10x retry mindkét location, 0.6 threshold, 5 perc interval
"""
import json
import time
import threading
from pathlib import Path

from library import ImageManager, safe_click, wait_random
from utils.logger import FarmLogger as log
from utils.queue_manager import queue_manager


class AllianceManager:
    """Alliance manager 5 perc timer-rel, 10x retry, 0.6 threshold"""
    
    def __init__(self):
        log.info("[Alliance] Manager inicializálva")
        self.config_dir = Path(__file__).parent.parent / 'config'
        self.images_dir = Path(__file__).parent.parent / 'images'
        
        # Config betöltés
        self.settings = self._load_settings()
        self.coords = self._load_coords()
        
        # Alliance config
        self.enabled = self.settings.get('alliance', {}).get('enabled', True)
        self.check_interval = self.settings.get('alliance', {}).get('check_interval_seconds', 300)  # ✅ 5 perc default
        
        # ✅ ÚJ: Retry config
        self.max_retries = 10  # 10x próbálkozás
        self.retry_delay = 1.0  # 1.0 sec delay retry-k között
        self.threshold = 0.6  # ✅ 0.6 threshold
        
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
    
    def _load_coords(self):
        """Alliance coords betöltése"""
        coords_file = self.config_dir / 'alliance_coords.json'
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def start(self):
        """Alliance Manager háttérszál indítása"""
        if not self.enabled:
            log.info("Alliance Manager disabled (config)")
            return
        
        if self.running:
            log.warning("Alliance Manager már fut!")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.thread.start()
        
        log.info(f"Alliance Manager elindult ({self.check_interval} sec interval)")
    
    def stop(self):
        """Alliance Manager leállítás"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        
        log.info("Alliance Manager leállítva")
    
    def _timer_loop(self):
        """
        Háttérszál: 5 percenként queue-ba task
        """
        while self.running:
            # Első trigger azonnal (induláskor)
            queue_manager.add_task("alliance_help", "alliance")
            log.info(f"[Alliance] Help task queue-ba téve")
            
            # Várakozás (5 perc, de 1 sec-enként ellenőrzi a running flag-et)
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def run_help(self, task_data=None):
        """
        Alliance help futtatás
        ✅ MÓDOSÍTVA: 10x retry mindkét location, 0.6 threshold
        """
        log.separator('=', 60)
        log.info("🤝 ALLIANCE HELP")
        log.separator('=', 60)
        
        hand_locations = self.coords.get('hand_locations', [])
        hand_template = self.images_dir / 'hand.png'
        
        if not hand_template.exists():
            log.warning(f"hand.png template nem található: {hand_template}")
            log.info("TODO: Setup Wizard-dal készítsd el a hand.png template-et")
            log.separator('=', 60)
            return
        
        log.info(f"[Alliance] hand.png keresés: {self.max_retries}x retry, threshold={self.threshold}")
        
        # ===== 10x RETRY LOOP =====
        for attempt in range(self.max_retries):
            log.separator('-', 60)
            log.info(f"[Alliance] Próbálkozás {attempt+1}/{self.max_retries}")
            log.separator('-', 60)
            
            # ===== LOCATION #1 =====
            if len(hand_locations) > 0:
                location_1 = hand_locations[0]
                x1, y1 = location_1.get('x', 0), location_1.get('y', 0)
                
                log.search(f"[Alliance] hand.png keresés location #1 ({x1}, {y1}) - threshold {self.threshold}...")
                
                coords = ImageManager.find_image(str(hand_template), threshold=self.threshold)  # ✅ 0.6
                
                if coords:
                    log.success(f"[Alliance] Hand megtalálva location #1 → {coords} ({attempt+1}. próba)")
                    
                    delay = wait_random(self.human_wait_min, self.human_wait_max)
                    log.wait(f"Várakozás {delay:.1f} mp")
                    time.sleep(delay)
                    
                    log.click(f"[Alliance] Hand kattintás → {coords}")
                    safe_click(coords)
                    
                    log.success("[Alliance] Help kattintás OK (location #1)")
                    log.separator('=', 60)
                    return
                else:
                    log.info(f"[Alliance] Location #1: Nem található ({attempt+1}/{self.max_retries})")
            
            # ===== LOCATION #2 =====
            if len(hand_locations) > 1:
                location_2 = hand_locations[1]
                x2, y2 = location_2.get('x', 0), location_2.get('y', 0)
                
                log.search(f"[Alliance] hand.png keresés location #2 ({x2}, {y2}) - threshold {self.threshold}...")
                
                coords = ImageManager.find_image(str(hand_template), threshold=self.threshold)  # ✅ 0.6
                
                if coords:
                    log.success(f"[Alliance] Hand megtalálva location #2 → {coords} ({attempt+1}. próba)")
                    
                    delay = wait_random(self.human_wait_min, self.human_wait_max)
                    log.wait(f"Várakozás {delay:.1f} mp")
                    time.sleep(delay)
                    
                    log.click(f"[Alliance] Hand kattintás → {coords}")
                    safe_click(coords)
                    
                    log.success("[Alliance] Help kattintás OK (location #2)")
                    log.separator('=', 60)
                    return
                else:
                    log.info(f"[Alliance] Location #2: Nem található ({attempt+1}/{self.max_retries})")
            
            # Várakozás retry előtt (kivéve utolsó próbálkozásnál)
            if attempt < self.max_retries - 1:
                log.wait(f"[Alliance] Várakozás {self.retry_delay} sec retry előtt...")
                time.sleep(self.retry_delay)
        
        # ===== VÉGLEG NEM TALÁLHATÓ =====
        log.separator('-', 60)
        log.info(f"[Alliance] hand.png nem található {self.max_retries} próbálkozás után (threshold={self.threshold})")
        log.info("[Alliance] Nincs help elérhető")
        log.separator('=', 60)
        
        # TODO kommentek
        log.info("[Alliance] TODO: Help All button implementation")
        log.info("[Alliance] TODO: Alliance event check")
        log.info("[Alliance] TODO: Gift collection")
        log.info("[Alliance] TODO: Territory gathering point check")


# Globális singleton instance
alliance_manager = AllianceManager()