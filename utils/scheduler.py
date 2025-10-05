"""
Auto Farm - Scheduler
Queue-ból task-ok futtatása (NEM szál, main loop hívja)
"""
from datetime import datetime
from utils.logger import FarmLogger as log


class Scheduler:
    """Task executor - Queue-ból task futtatás"""
    
    def __init__(self):
        # Jelenleg futó task
        self.current_task = None
        self.task_start_time = None
        
        # Manager importok (később, lazy import)
        self._gathering_manager = None
        self._training_manager = None
        self._alliance_manager = None
        self._anti_afk_manager = None
    
    def tick(self):
        """
        Fő ciklus (main loop hívja 10 sec-enként)
        
        Returns:
            bool: True ha futott task, False ha nem
        """
        # Ha már fut task, skip
        if self.is_task_running():
            return False
        
        # Queue peek
        from utils.queue_manager import queue_manager
        next_task = queue_manager.peek_next_task()
        
        # Ha üres queue
        if not next_task:
            return False
        
        # Task futtatás
        log.separator('=', 60)
        log.action(f"Scheduler: Task futtatása → {next_task['task_id']} ({next_task['type']})")
        log.separator('=', 60)
        
        # Queue-ból kivétel (get_next törli is)
        queue_manager.get_next_task()
        
        # Task execute
        self.execute_task(next_task)
        
        return True
    
    def execute_task(self, task):
        """
        Task futtatás típus szerint
        
        Args:
            task: Task dict
        """
        try:
            self.mark_task_started(task)
            
            task_type = task.get('type')
            task_data = task.get('data', {})
            
            # Típus alapján manager hívás
            if task_type == 'gathering':
                self._execute_gathering(task, task_data)
            
            elif task_type == 'training':
                self._execute_training(task, task_data)
            
            elif task_type == 'alliance':
                self._execute_alliance(task, task_data)
            
            elif task_type == 'anti_afk':
                self._execute_anti_afk(task, task_data)
            
            else:
                log.warning(f"Ismeretlen task típus: {task_type}")
            
            self.mark_task_finished()
        
        except Exception as e:
            log.error(f"Task futtatási hiba: {e}")
            import traceback
            traceback.print_exc()
            self.mark_task_finished()
    
    def _execute_gathering(self, task, task_data):
        """Gathering task futtatás"""
        if self._gathering_manager is None:
            from managers.gathering_manager import gathering_manager
            self._gathering_manager = gathering_manager
        
        commander_id = task_data.get('commander_id', 1)
        log.info(f"Gathering Manager hívás: Commander #{commander_id}")
        
        result = self._gathering_manager.run_commander(commander_id, task_data)
        
        if result == "RESTART":
            log.warning("Gathering restart szükséges!")
            # TODO: Re-queue task?
    
    def _execute_training(self, task, task_data):
        """Training task futtatás"""
        if self._training_manager is None:
            from managers.training_manager import training_manager
            self._training_manager = training_manager
        
        building = task_data.get('building', 'barracks')
        log.info(f"Training Manager hívás: {building}")
        
        self._training_manager.restart_training(task_data)
    
    def _execute_alliance(self, task, task_data):
        """Alliance task futtatás"""
        if self._alliance_manager is None:
            from managers.alliance_manager import alliance_manager
            self._alliance_manager = alliance_manager
        
        log.info("Alliance Manager hívás: Help")
        
        self._alliance_manager.run_help(task_data)
    
    def _execute_anti_afk(self, task, task_data):
        """Anti-AFK task futtatás"""
        if self._anti_afk_manager is None:
            from managers.anti_afk_manager import anti_afk_manager
            self._anti_afk_manager = anti_afk_manager
        
        log.info("Anti-AFK Manager hívás: Resource collection")
        
        self._anti_afk_manager.collect_resources(task_data)
    
    def mark_task_started(self, task):
        """
        Task indítás jelzés
        
        Args:
            task: Task dict
        """
        self.current_task = task
        self.task_start_time = datetime.now()
        log.info(f"Task indítva: {task['task_id']}")
    
    def mark_task_finished(self):
        """Task befejezés jelzés"""
        if self.current_task:
            duration = (datetime.now() - self.task_start_time).total_seconds()
            log.success(f"Task befejezve: {self.current_task['task_id']} ({duration:.1f} sec)")
        
        self.current_task = None
        self.task_start_time = None
    
    def is_task_running(self):
        """
        Van-e jelenleg futó task?
        
        Returns:
            bool: True ha van futó task
        """
        return self.current_task is not None
    
    def get_current_task(self):
        """
        Jelenleg futó task lekérése
        
        Returns:
            dict: Task vagy None
        """
        if self.current_task:
            return self.current_task.copy()
        return None


# Globális singleton instance
scheduler = Scheduler()


# ===== TESZT =====
if __name__ == "__main__":
    print("="*60)
    print("SCHEDULER TESZT")
    print("="*60)
    
    from utils.queue_manager import queue_manager
    
    # Queue tisztítás
    queue_manager.clear_queue()
    
    # Test task hozzáadás
    print("\n1. Test task hozzáadás:")
    queue_manager.add_task("test_task_1", "gathering", {"commander_id": 1})
    
    # Scheduler tick (nincs manager, mock)
    print("\n2. Scheduler tick (manager nincs, hiba várható):")
    try:
        result = scheduler.tick()
        print(f"  Tick result: {result}")
    except Exception as e:
        print(f"  Hiba (várható): {e}")
    
    # Task running check
    print("\n3. Task running check:")
    print(f"  Van futó task? {scheduler.is_task_running()}")
    
    print("\n" + "="*60)
    print("TESZT VÉGE")
    print("Figyelem: Manager-ek nincsenek implementálva, hibás futás várható!")
    print("="*60)