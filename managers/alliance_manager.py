"""
Auto Farm - Alliance Manager
Alliance help 30 perces timer-rel
"""
import json
import time
import threading
from pathlib import Path

from library import ImageManager, safe_click, wait_random
from utils.logger import FarmLogger as log
from utils.queue_manager import queue_manager


class AllianceManager:
    """Alliance manager 30 perc timer-rel"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / 'config'
        self.images_dir = Path(__file__).parent.parent / 'images'
        
        # Config betöltés
        self.settings = self._load_settings()
        self.coords = self._load_coords()
        
        # Alliance config
        self.enabled = self.settings.get('alliance', {}).get('enabled', True)
        self.check_interval = self.settings.get('alliance', {}).get('check_interval_seconds', 1800)
        
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
        Háttérszál: 30 percenként queue-ba task
        """
        while self.running:
            # Első trigger azonnal (induláskor)
            queue_manager.add_task("alliance_help", "alliance")
            log.info(f"[Alliance] Help task queue-ba téve")
            
            # Várakozás (30 perc, de 1 sec-enként ellenőrzi a running flag-et)
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def run_help(self, task_data=None):
        """
        Alliance help futtatás
        
        hand.png keresés 2 koordinátán
        """
        log.separator('=', 60)
        log.info("🤝 ALLIANCE HELP")
        log.separator('=', 60)
        
        hand_locations = self.coords.get('hand_locations', [])
        hand_template = self.images_dir / 'hand.png'
        
        if not hand_template.exists():
            log.warning(f"hand.png template nem található: {hand_template}")
            log.info("TODO: Setup Wizard-dal készítsd el a hand.png template-et")
            return
        
        # Hand keresés location #1
        if len(hand_locations) > 0:
            location_1 = hand_locations[0]
            x1, y1 = location_1.get('x', 0), location_1.get('y', 0)
            
            log.search(f"hand.png keresés location #1 ({x1}, {y1})...")
            
            # TODO: Region-based template match (jelenleg teljes képernyő)
            coords = ImageManager.find_image(str(hand_template), threshold=0.7)
            
            if coords:
                log.success(f"Hand megtalálva location #1 → {coords}")
                
                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"Várakozás {delay:.1f} mp")
                time.sleep(delay)
                
                safe_click(coords)
                log.success("Alliance help kattintás OK")
                log.separator('=', 60)
                return
        
        # Hand keresés location #2
        if len(hand_locations) > 1:
            location_2 = hand_locations[1]
            x2, y2 = location_2.get('x', 0), location_2.get('y', 0)
            
            log.search(f"hand.png keresés location #2 ({x2}, {y2})...")
            
            coords = ImageManager.find_image(str(hand_template), threshold=0.7)
            
            if coords:
                log.success(f"Hand megtalálva location #2 → {coords}")
                
                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"Várakozás {delay:.1f} mp")
                time.sleep(delay)
                
                safe_click(coords)
                log.success("Alliance help kattintás OK")
                log.separator('=', 60)
                return
        
        # Ha nem találtuk
        log.info("hand.png nem található egyik helyen sem (nincs help)")
        log.separator('=', 60)
        
        # TODO kommentek
        log.info("TODO: Help All button implementation")
        log.info("TODO: Alliance event check")
        log.info("TODO: Gift collection")
        log.info("TODO: Territory gathering point check")


# Globális singleton instance
alliance_manager = AllianceManager()


# ===== TESZT =====
if __name__ == "__main__":
    log.separator('=', 60)
    log.info("ALLIANCE MANAGER TESZT")
    log.separator('=', 60)
    
    # Start (háttérszál)
    alliance_manager.start()
    
    # Várakozás 5 sec (teszteléshez)
    log.info("Várakozás 5 sec...")
    time.sleep(5)
    
    # Stop
    alliance_manager.stop()
    
    log.separator('=', 60)
    log.info("TESZT VÉGE")
    log.separator('=', 60)