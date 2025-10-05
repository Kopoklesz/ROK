"""
Auto Farm - Anti-AFK Manager
15 perc idle után resource collection
"""
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta

from library import ImageManager, safe_click, wait_random
from utils.logger import FarmLogger as log
from utils.queue_manager import queue_manager


class AntiAFKManager:
    """Anti-AFK manager idle detection-nel"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / 'config'
        self.images_dir = Path(__file__).parent.parent / 'images'
        
        # Config betöltés
        self.settings = self._load_settings()
        
        # Anti-AFK config
        self.enabled = self.settings.get('anti_afk', {}).get('enabled', True)
        self.idle_threshold = self.settings.get('anti_afk', {}).get('idle_threshold_seconds', 900)
        self.resource_offset_y = self.settings.get('anti_afk', {}).get('resource_offset_y', 50)
        
        # Thread control
        self.running = False
        self.thread = None
        
        # Idle check interval (60 sec)
        self.check_interval = 60
        
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
    
    def start(self):
        """Anti-AFK Manager háttérszál indítása"""
        if not self.enabled:
            log.info("Anti-AFK Manager disabled (config)")
            return
        
        if self.running:
            log.warning("Anti-AFK Manager már fut!")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._idle_check_loop, daemon=True)
        self.thread.start()
        
        log.info(f"Anti-AFK Manager elindult ({self.idle_threshold} sec idle threshold)")
    
    def stop(self):
        """Anti-AFK Manager leállítás"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        
        log.info("Anti-AFK Manager leállítva")
    
    def _idle_check_loop(self):
        """
        Háttérszál: 60 sec-enként idle check
        """
        while self.running:
            # Idle check
            last_log_time = log.get_last_log_time()
            
            if last_log_time is None:
                # Még nincs log (indulás után)
                log.info("[Anti-AFK] Nincs még log entry, skip")
            else:
                # Idle idő számítás
                now = datetime.now()
                idle_seconds = (now - last_log_time).total_seconds()
                
                # Ha idle >= threshold
                if idle_seconds >= self.idle_threshold:
                    log.warning(f"[Anti-AFK] {idle_seconds:.0f} sec idle detected! (threshold: {self.idle_threshold})")
                    
                    # PRIORITÁSOS task queue-ba
                    queue_manager.add_priority_task("anti_afk_collect", "anti_afk")
                    log.info("[Anti-AFK] Resource collection task hozzáadva (PRIORITÁS)")
            
            # Várakozás (60 sec, de 1 sec-enként ellenőrzi a running flag-et)
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def collect_resources(self, task_data=None):
        """
        Resource collection (4 képből első találat)
        """
        log.separator('=', 60)
        log.info("🔄 ANTI-AFK RESOURCE COLLECTION")
        log.separator('=', 60)
        
        resource_templates = [
            self.images_dir / 'resource1.png',
            self.images_dir / 'resource2.png',
            self.images_dir / 'resource3.png',
            self.images_dir / 'resource4.png'
        ]
        
        for i, template_path in enumerate(resource_templates, 1):
            if not template_path.exists():
                log.warning(f"resource{i}.png template nem található: {template_path}")
                continue
            
            log.search(f"resource{i}.png keresés...")
            
            coords = ImageManager.find_image(str(template_path), threshold=0.7)
            
            if coords:
                log.success(f"resource{i}.png megtalálva → {coords}")
                
                # Kattintás Y + offset (alá kattintás)
                click_x = coords[0]
                click_y = coords[1] + self.resource_offset_y
                
                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"Várakozás {delay:.1f} mp")
                time.sleep(delay)
                
                log.click(f"Resource kattintás → ({click_x}, {click_y})")
                safe_click((click_x, click_y))
                
                log.success("Anti-AFK resource collection OK")
                log.separator('=', 60)
                return
        
        # Ha egyik sem találtuk
        log.info("Egyik resource template sem található (nincs resource)")
        log.separator('=', 60)


# Globális singleton instance
anti_afk_manager = AntiAFKManager()


# ===== TESZT =====
if __name__ == "__main__":
    log.separator('=', 60)
    log.info("ANTI-AFK MANAGER TESZT")
    log.separator('=', 60)
    
    # Logger inicializálás (teszt)
    log.initialize()
    
    # Start (háttérszál)
    anti_afk_manager.start()
    
    # Várakozás 5 sec
    log.info("Várakozás 5 sec...")
    time.sleep(5)
    
    # Stop
    anti_afk_manager.stop()
    
    log.separator('=', 60)
    log.info("TESZT VÉGE")
    log.separator('=', 60)