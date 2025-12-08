"""
Auto Farm - Queue Manager
FIFO task queue thread-safe implementáció JSON persistence-szel
"""
import json
import threading
from pathlib import Path
from datetime import datetime


class QueueManager:
    """Thread-safe FIFO task queue JSON mentéssel"""
    
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / 'config'
        
        self.config_dir = Path(config_dir)
        self.queue_file = self.config_dir / 'task_queue.json'
        
        # Thread lock
        self.lock = threading.Lock()
        
        # Queue (list)
        self.queue = []
        
        # Automatikus betöltés
        self.load_from_file()
    
    def add_task(self, task_id, task_type, data=None, status="pending"):
        """
        Task hozzáadása queue végére

        Args:
            task_id: Egyedi azonosító (pl. "commander_1_restart")
            task_type: Task típus ("gathering", "training", "alliance", "anti_afk")
            data: Opcionális extra adat (dict)
            status: Task állapot ("pending", "sending", "marching", "gathering", "returning")
        """
        with self.lock:
            task = {
                "task_id": task_id,
                "type": task_type,
                "status": status,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": data or {}
            }

            self.queue.append(task)
            self._log_action(f"Task hozzáadva: {task_id} ({task_type}, status={status})")
            self.save_to_file()
    
    def add_priority_task(self, task_id, task_type, data=None, status="pending"):
        """
        PRIORITÁSOS task hozzáadása (queue elejére)
        Anti-AFK használja

        Args:
            task_id: Egyedi azonosító
            task_type: Task típus
            data: Opcionális extra adat
            status: Task állapot
        """
        with self.lock:
            task = {
                "task_id": task_id,
                "type": task_type,
                "status": status,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": data or {}
            }

            self.queue.insert(0, task)  # Elejére!
            self._log_action(f"PRIORITÁS task hozzáadva: {task_id} ({task_type}, status={status})")
            self.save_to_file()
    
    def get_next_task(self):
        """
        Következő task lekérése ÉS törlése (FIFO)
        
        Returns:
            dict: Task vagy None ha üres
        """
        with self.lock:
            if not self.queue:
                return None
            
            task = self.queue.pop(0)
            self._log_action(f"Task kivéve: {task['task_id']} ({task['type']})")
            self.save_to_file()
            return task
    
    def peek_next_task(self):
        """
        Következő task lekérése törlés NÉLKÜL
        
        Returns:
            dict: Task vagy None ha üres
        """
        with self.lock:
            if not self.queue:
                return None
            
            return self.queue[0].copy()  # Másolat (ne módosítsa kívülről)
    
    def remove_task(self, task_id):
        """
        Adott task törlése ID alapján
        
        Args:
            task_id: Task azonosító
            
        Returns:
            bool: Sikeres törlés
        """
        with self.lock:
            for i, task in enumerate(self.queue):
                if task['task_id'] == task_id:
                    del self.queue[i]
                    self._log_action(f"Task törölve: {task_id}")
                    self.save_to_file()
                    return True
            
            return False
    
    def get_all_tasks(self):
        """
        Teljes queue lista lekérése
        
        Returns:
            list: Összes task (másolat)
        """
        with self.lock:
            return [task.copy() for task in self.queue]
    
    def clear_queue(self):
        """Teljes queue törlése"""
        with self.lock:
            count = len(self.queue)
            self.queue = []
            self._log_action(f"Queue törölve ({count} task)")
            self.save_to_file()

    def cleanup_on_startup(self):
        """
        Induláskor régi/érvénytelen taskok törlése

        Törli:
        - Összes taskot (clean slate)
        """
        with self.lock:
            count = len(self.queue)
            if count > 0:
                self.queue = []
                self._log_action(f"[STARTUP CLEANUP] Queue törölve ({count} régi task eltávolítva)")
                self.save_to_file()
            else:
                self._log_action("[STARTUP CLEANUP] Queue üres, nincs teendő")
    
    def get_queue_size(self):
        """Queue méret"""
        with self.lock:
            return len(self.queue)

    def update_task_status(self, task_id, status):
        """
        Task állapot frissítése

        Args:
            task_id: Task azonosító
            status: Új állapot ("pending", "sending", "marching", "gathering", "returning")

        Returns:
            bool: Sikeres frissítés
        """
        with self.lock:
            for task in self.queue:
                if task['task_id'] == task_id:
                    old_status = task.get('status', 'unknown')
                    task['status'] = status
                    self._log_action(f"Task status frissítve: {task_id} ({old_status} → {status})")
                    self.save_to_file()
                    return True

            return False

    def get_current_task(self):
        """
        Aktuális (első) task lekérése törlés NÉLKÜL
        (Alias peek_next_task-hez, szemantikailag beszédesebb connection monitor számára)

        Returns:
            dict: Task vagy None ha üres
        """
        return self.peek_next_task()

    def requeue_task(self, task):
        """
        Task visszahelyezése a queue elejére (pl. connection lost után újraindítás)

        Args:
            task: Task dict
        """
        with self.lock:
            # Reset status
            task['status'] = 'pending'
            task['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Queue elejére
            self.queue.insert(0, task)
            self._log_action(f"Task újra queue-ba: {task['task_id']} ({task['type']})")
            self.save_to_file()

    def save_to_file(self):
        """Queue mentése JSON fájlba"""
        try:
            # Könyvtár létrehozása ha kell
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(self.queue, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Queue mentési hiba: {e}")
    
    def load_from_file(self):
        """Queue betöltése JSON fájlból"""
        try:
            if self.queue_file.exists():
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.queue = json.loads(content)
                        self._log_action(f"Queue betöltve: {len(self.queue)} task")
                    else:
                        self.queue = []
            else:
                self.queue = []
        
        except Exception as e:
            print(f"Queue betöltési hiba: {e}")
            self.queue = []
    
    def _log_action(self, message):
        """Logging queue műveletekhez"""
        try:
            from utils.logger import FarmLogger as log
            log.info(f"[Queue] {message}")
        except:
            # Ha logger még nincs inicializálva
            print(f"[Queue] {message}")


# Globális singleton instance
queue_manager = QueueManager()


# ===== TESZT =====
if __name__ == "__main__":
    print("="*60)
    print("QUEUE MANAGER TESZT")
    print("="*60)
    
    # Tiszta slate
    queue_manager.clear_queue()
    
    # Task hozzáadás
    print("\n1. Task hozzáadás:")
    queue_manager.add_task("commander_1_start", "gathering", {"commander_id": 1})
    queue_manager.add_task("commander_2_start", "gathering", {"commander_id": 2})
    queue_manager.add_task("barracks_restart", "training", {"building": "barracks"})
    
    # Queue lista
    print("\n2. Queue lista:")
    tasks = queue_manager.get_all_tasks()
    for task in tasks:
        print(f"  - {task['task_id']} ({task['type']}) @ {task['timestamp']}")
    
    # Prioritás task
    print("\n3. Prioritás task (anti-afk):")
    queue_manager.add_priority_task("anti_afk_collect", "anti_afk")
    
    tasks = queue_manager.get_all_tasks()
    print("  Queue sorrend:")
    for task in tasks:
        print(f"  - {task['task_id']} ({task['type']})")
    
    print("\n" + "="*60)
    print("TESZT VÉGE")
    print(f"Queue fájl: {queue_manager.queue_file}")
    print("="*60)