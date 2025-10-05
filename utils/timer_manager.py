"""
Auto Farm - Timer Manager
Háttérszálon futó timer rendszer deadline kezeléssel
"""
import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta


class TimerManager:
    """Háttérszálon futó timer manager deadline callback-kel"""
    
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / 'config'
        
        self.config_dir = Path(config_dir)
        self.timers_file = self.config_dir / 'timers.json'
        
        # Thread lock
        self.lock = threading.Lock()
        
        # Timers lista
        self.timers = []
        
        # Thread control
        self.running = False
        self.thread = None
        
        # Tick interval (másodperc)
        self.tick_interval = 10
        
        # Automatikus betöltés
        self.load_from_file()
    
    def add_timer(self, timer_id, deadline_seconds, task_id, task_type, data=None):
        """
        Timer hozzáadása
        
        Args:
            timer_id: Timer azonosító (pl. "commander_1")
            deadline_seconds: Hány mp múlva járjon le
            task_id: Queue-ba tett task ID
            task_type: Task típus ("gathering", "training", stb.)
            data: Opcionális extra adat
        """
        with self.lock:
            # Deadline számítás
            deadline = datetime.now() + timedelta(seconds=deadline_seconds)
            deadline_str = deadline.strftime("%Y-%m-%d %H:%M:%S")
            
            timer = {
                "timer_id": timer_id,
                "deadline": deadline_str,
                "callback_type": "queue_add",
                "callback_data": {
                    "task_id": task_id,
                    "task_type": task_type,
                    "data": data or {}
                }
            }
            
            # Ha már létezik ilyen timer_id, töröljük
            self.timers = [t for t in self.timers if t['timer_id'] != timer_id]
            
            self.timers.append(timer)
            self._log_action(f"Timer hozzáadva: {timer_id} → {deadline_seconds}s múlva ({deadline_str})")
            self.save_to_file()
    
    def remove_timer(self, timer_id):
        """
        Timer törlése
        
        Args:
            timer_id: Timer azonosító
            
        Returns:
            bool: Sikeres törlés
        """
        with self.lock:
            before_count = len(self.timers)
            self.timers = [t for t in self.timers if t['timer_id'] != timer_id]
            
            if len(self.timers) < before_count:
                self._log_action(f"Timer törölve: {timer_id}")
                self.save_to_file()
                return True
            
            return False
    
    def get_all_timers(self):
        """
        Összes timer lista
        
        Returns:
            list: Timer lista (másolat)
        """
        with self.lock:
            return [t.copy() for t in self.timers]
    
    def start(self):
        """Háttérszál indítása"""
        if self.running:
            self._log_action("Timer Manager már fut!")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._tick_loop, daemon=True)
        self.thread.start()
        self._log_action("Timer Manager elindult (10 sec tick)")
    
    def stop(self):
        """Háttérszál leállítása"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        
        self._log_action("Timer Manager leállítva")
    
    def _tick_loop(self):
        """Fő ciklus (10 sec tick)"""
        while self.running:
            try:
                self._check_deadlines()
            except Exception as e:
                self._log_action(f"Tick hiba: {e}")
            
            # Várakozás (10 sec, de 1 sec-enként ellenőrzi a running flag-et)
            for _ in range(self.tick_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def _check_deadlines(self):
        """Lejárt timer-ek keresése és callback futtatás"""
        now = datetime.now()
        
        with self.lock:
            expired_timers = []
            
            for timer in self.timers:
                deadline = datetime.strptime(timer['deadline'], "%Y-%m-%d %H:%M:%S")
                
                if now >= deadline:
                    expired_timers.append(timer)
            
            # Lejárt timer-ek törlése
            if expired_timers:
                for timer in expired_timers:
                    self.timers.remove(timer)
                    self._log_action(f"Timer lejárt: {timer['timer_id']}")
                
                self.save_to_file()
        
        # Callback-ek futtatása (lock-on kívül!)
        for timer in expired_timers:
            self._execute_callback(timer)
    
    def _execute_callback(self, timer):
        """
        Timer callback futtatása
        
        Args:
            timer: Timer dict
        """
        try:
            callback_type = timer.get('callback_type')
            callback_data = timer.get('callback_data', {})
            
            if callback_type == 'queue_add':
                # Queue Manager-be task hozzáadás
                from utils.queue_manager import queue_manager
                
                task_id = callback_data.get('task_id')
                task_type = callback_data.get('task_type')
                data = callback_data.get('data')
                
                queue_manager.add_task(task_id, task_type, data)
                self._log_action(f"Callback futott: {task_id} hozzáadva queue-hoz")
        
        except Exception as e:
            self._log_action(f"Callback hiba: {e}")
    
    def save_to_file(self):
        """Timer-ek mentése JSON-ba"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.timers_file, 'w', encoding='utf-8') as f:
                json.dump(self.timers, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Timer mentési hiba: {e}")
    
    def load_from_file(self):
        """Timer-ek betöltése JSON-ból"""
        try:
            if self.timers_file.exists():
                with open(self.timers_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.timers = json.loads(content)
                        self._log_action(f"Timer-ek betöltve: {len(self.timers)} db")
                    else:
                        self.timers = []
            else:
                self.timers = []
        
        except Exception as e:
            print(f"Timer betöltési hiba: {e}")
            self.timers = []
    
    def _log_action(self, message):
        """Logging timer műveletekhez"""
        try:
            from utils.logger import FarmLogger as log
            log.info(f"[Timer] {message}")
        except:
            # Ha logger még nincs inicializálva
            print(f"[Timer] {message}")


# Globális singleton instance
timer_manager = TimerManager()


# ===== TESZT =====
if __name__ == "__main__":
    print("="*60)
    print("TIMER MANAGER TESZT")
    print("="*60)
    
    from utils.queue_manager import queue_manager
    
    # Queue tisztítás
    queue_manager.clear_queue()
    
    # Timer Manager indítás
    print("\n1. Timer Manager indítás:")
    timer_manager.start()
    
    # Timer hozzáadás (5 sec)
    print("\n2. Timer hozzáadás (5 sec):")
    timer_manager.add_timer(
        timer_id="test_timer_1",
        deadline_seconds=5,
        task_id="test_task_1",
        task_type="gathering"
    )
    
    # Timer hozzáadás (10 sec)
    print("\n3. Timer hozzáadás (10 sec):")
    timer_manager.add_timer(
        timer_id="test_timer_2",
        deadline_seconds=10,
        task_id="test_task_2",
        task_type="training"
    )
    
    # Timer lista
    print("\n4. Aktív timer-ek:")
    timers = timer_manager.get_all_timers()
    for t in timers:
        print(f"  - {t['timer_id']} → {t['deadline']}")
    
    # Várakozás 6 sec
    print("\n5. Várakozás 6 sec (timer_1 lejár)...")
    time.sleep(6)
    
    # Queue ellenőrzés
    print("\n6. Queue ellenőrzés:")
    tasks = queue_manager.get_all_tasks()
    if tasks:
        print(f"  Queue: {tasks[0]['task_id']} (várhatóan: test_task_1)")
    else:
        print("  Queue üres (hiba!)")
    
    # Várakozás további 5 sec
    print("\n7. Várakozás további 5 sec (timer_2 lejár)...")
    time.sleep(5)
    
    # Queue ellenőrzés újra
    print("\n8. Queue ellenőrzés:")
    tasks = queue_manager.get_all_tasks()
    print(f"  Queue méret: {len(tasks)} (várhatóan: 2)")
    for task in tasks:
        print(f"  - {task['task_id']}")
    
    # Timer Manager leállítás
    print("\n9. Timer Manager leállítás:")
    timer_manager.stop()
    
    print("\n" + "="*60)
    print("TESZT VÉGE")
    print(f"Timers fájl: {timer_manager.timers_file}")
    print("="*60)