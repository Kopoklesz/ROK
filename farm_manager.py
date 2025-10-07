"""
ROK Auto Farm Manager - Orchestrator
Új architektúra: Queue + Timer + Scheduler + Managers
"""
import time
import signal
import sys

from library import initialize_game_window
from utils.logger import FarmLogger as log
from utils.queue_manager import queue_manager
from utils.timer_manager import timer_manager
from utils.scheduler import scheduler

from managers.gathering_manager import gathering_manager
from managers.training_manager import training_manager
from managers.alliance_manager import alliance_manager
from managers.anti_afk_manager import anti_afk_manager


def signal_handler(sig, frame):
    """CTRL+C graceful shutdown"""
    log.separator('#', 60)
    log.warning("⚠️  CTRL+C - Leállítás...")
    log.separator('#', 60)
    
    # Managers leállítás
    log.info("Timer Manager leállítás...")
    timer_manager.stop()
    
    log.info("Training Manager leállítás...")
    training_manager.stop()
    
    log.info("Alliance Manager leállítás...")
    alliance_manager.stop()
    
    log.info("Anti-AFK Manager leállítás...")
    anti_afk_manager.stop()
    
    # Queue & Timer mentés
    log.info("Queue mentése...")
    queue_manager.save_to_file()
    
    log.info("Timer-ek mentése...")
    timer_manager.save_to_file()
    
    # Logger bezárás
    log.info("Logger bezárása...")
    log.close()
    
    log.separator('#', 60)
    log.success("✅ Graceful shutdown befejezve")
    log.separator('#', 60)
    
    sys.exit(0)


def main():
    """Main orchestrator"""
    
    # Signal handler (CTRL+C)
    signal.signal(signal.SIGINT, signal_handler)
    
    # ===== 1. LOGGER INICIALIZÁLÁS =====
    log.separator('#', 60)
    log.info("🚀 ROK AUTO FARM MANAGER - ORCHESTRATOR")
    log.separator('#', 60)
    
    log.initialize()
    log.success("Logger inicializálva (file logging enabled)")
    
    # ===== 2. JÁTÉK ABLAK INICIALIZÁLÁS =====
    log.separator('=', 60)
    log.info("Játék ablak inicializálás...")
    log.separator('=', 60)
    
    if not initialize_game_window("BlueStacks"):
        log.error("❌ Játék ablak nem található!")
        log.info("Módosítsd a 'BlueStacks' szöveget a library.py-ban a játék ablak nevére.")
        return
    
    log.success("Játék ablak OK")
    
    # ===== 3. QUEUE MANAGER INIT =====
    log.separator('=', 60)
    log.info("Queue Manager inicializálás...")
    log.separator('=', 60)
    
    queue_size = queue_manager.get_queue_size()
    log.info(f"Queue betöltve: {queue_size} task")
    
    # ===== 4. TIMER MANAGER START =====
    log.separator('=', 60)
    log.info("Timer Manager indítás...")
    log.separator('=', 60)
    
    timer_manager.start()
    
    timers = timer_manager.get_all_timers()
    log.info(f"Aktív timer-ek: {len(timers)} db")
    
    # ===== 5. SCHEDULER INIT =====
    log.separator('=', 60)
    log.info("Scheduler inicializálás...")
    log.separator('=', 60)
    
    log.success("Scheduler készen áll")
    
    # ===== 6. GATHERING MANAGER INIT =====
    log.separator('=', 60)
    log.info("Gathering Manager inicializálás...")
    log.separator('=', 60)
    
    # Első commanders start (queue-ba)
    gathering_manager.start()
    
    # ===== 7. TRAINING MANAGER START =====
    log.separator('=', 60)
    log.info("Training Manager indítás...")
    log.separator('=', 60)
    
    training_manager.start()
    
    # ===== 8. ALLIANCE MANAGER START =====
    log.separator('=', 60)
    log.info("Alliance Manager indítás...")
    log.separator('=', 60)
    
    alliance_manager.start()
    
    # ===== 9. ANTI-AFK MANAGER START =====
    log.separator('=', 60)
    log.info("Anti-AFK Manager indítás...")
    log.separator('=', 60)
    
    anti_afk_manager.start()
    
    # ===== 10. MAIN LOOP =====
    log.separator('#', 60)
    log.success("✅ ÖSSZES MANAGER ELINDULT - MAIN LOOP KEZDŐDIK")
    log.separator('#', 60)
    
    log.info("Main Loop: Scheduler tick minden 10 másodpercben")
    log.info("CTRL+C = graceful shutdown")
    log.separator('#', 60)
    
    tick_count = 0
    
    try:
        while True:
            tick_count += 1
            
            # Scheduler tick
            task_executed = scheduler.tick()
            
            if not task_executed:
                # Csak minden 10. tick-nél log (100 sec = ~1.5 perc)
                if tick_count % 10 == 0:
                    queue_size = queue_manager.get_queue_size()
                    log.info(f"[Tick {tick_count}] Queue üres, várakozás... (Queue: {queue_size}, Timers: {len(timer_manager.get_all_timers())})")
            
            # Várakozás 10 sec
            time.sleep(10)
    
    except KeyboardInterrupt:
        # CTRL+C - signal handler kezeli
        pass
    
    except Exception as e:
        log.separator('#', 60)
        log.error(f"KRITIKUS HIBA A MAIN LOOP-BAN: {str(e)}")
        log.separator('#', 60)
        import traceback
        traceback.print_exc()
        
        # Graceful shutdown
        signal_handler(None, None)


if __name__ == "__main__":
    main()