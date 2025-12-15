"""
ROK Auto Farm - Connection Monitor
Internet megszakadás detektálás és helyreállítás
"""
import time
import json
import threading
from pathlib import Path

from library import safe_click, ImageManager, wait_random
from utils.logger import FarmLogger as log
from utils.queue_manager import queue_manager
from utils.timer_manager import timer_manager


class ConnectionMonitor:
    """
    Connection Lost ablak figyelés és helyreállítás

    Működés:
    1. Háttérben fut (background thread)
    2. Periodikusan ellenőrzi (pl. 5 másodpercenként) hogy megjelent-e a "Connection Lost" ablak
    3. Ha igen:
       - Aktuális task lekérése
       - Állapot függő helyreállítás
       - Confirm gomb kattintás
       - 30 sec várakozás
       - Task folytatása/újraindítása
    """

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / 'config'
        self.config_file = self.config_dir / 'connection_monitor.json'

        # Config betöltés
        self.load_config()

        # Human wait (settings.json-ból)
        settings_file = self.config_dir / 'settings.json'
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                human_wait = settings.get('human_wait', {})
                self.human_wait_min = human_wait.get('min_seconds', 5)
                self.human_wait_max = human_wait.get('max_seconds', 10)
        else:
            self.human_wait_min = 5
            self.human_wait_max = 10

        # Monitor thread
        self.running = False
        self.thread = None

    def load_config(self):
        """Config betöltése"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            # Default config
            config = {
                "enabled": False,
                "check_interval_seconds": 5,
                "detection_region": None,
                "detection_text": "NETWORK DISCONNECTED",
                "confirm_button": None,
                "recovery_wait_seconds": 120,  # 2 perc várakozás CONFIRM után
                "default_recovery_time_seconds": 5400  # 1.5 óra = 90 perc
            }

        self.enabled = config.get('enabled', False)
        self.check_interval = config.get('check_interval_seconds', 5)
        self.detection_region = config.get('detection_region')
        self.detection_text = config.get('detection_text', 'NETWORK DISCONNECTED')
        self.confirm_button = config.get('confirm_button')
        self.recovery_wait = config.get('recovery_wait_seconds', 120)  # 2 perc default
        self.default_recovery_time = config.get('default_recovery_time_seconds', 5400)

    def start(self):
        """Monitor indítása"""
        if not self.enabled:
            log.info("[ConnectionMonitor] Disabled, skip")
            return

        if self.running:
            log.warning("[ConnectionMonitor] Már fut!")
            return

        if not self.detection_region or not self.confirm_button:
            log.error("[ConnectionMonitor] Config hiányos! Használd a Setup Wizard-ot.")
            return

        log.separator('=', 60)
        log.info("[ConnectionMonitor] Monitor indítása...")
        log.info(f"[ConnectionMonitor] Check interval: {self.check_interval} sec")
        log.info(f"[ConnectionMonitor] Detection text: '{self.detection_text}'")
        log.separator('=', 60)

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

        log.success("[ConnectionMonitor] Monitor elindítva")

    def stop(self):
        """Monitor leállítása"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

        log.info("[ConnectionMonitor] Monitor leállítva")

    def _monitor_loop(self):
        """Monitor háttérszál"""
        while self.running:
            try:
                # Connection lost ellenőrzés
                if self._check_connection_lost():
                    log.error("="*60)
                    log.error("[CONNECTION LOST] Internet megszakadás észlelve!")
                    log.error("="*60)

                    # Helyreállítás
                    self._handle_connection_lost()

                # Várakozás
                time.sleep(self.check_interval)

            except Exception as e:
                log.error(f"[ConnectionMonitor] Monitor hiba: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(self.check_interval)

    def _check_connection_lost(self):
        """
        Connection Lost ablak ellenőrzése OCR-rel

        Returns:
            bool: True ha megjelent
        """
        if not self.detection_region:
            return False

        try:
            # OCR a detection region-ön
            ocr_text = ImageManager.read_text_from_region(self.detection_region)

            if not ocr_text:
                return False

            # Tartalmazza a keresett szöveget?
            if self.detection_text.lower() in ocr_text.lower():
                log.warning(f"[ConnectionMonitor] Connection Lost detected! OCR: '{ocr_text}'")
                return True

            return False

        except Exception as e:
            log.error(f"[ConnectionMonitor] Check hiba: {e}")
            return False

    def _handle_connection_lost(self):
        """Connection lost helyreállítás"""
        try:
            # 1. Aktuális task lekérése
            current_task = queue_manager.get_current_task()

            if not current_task:
                log.info("[Recovery] Nincs aktív task")
                self._click_confirm_and_wait()
                return

            task_id = current_task.get('task_id', 'unknown')
            task_type = current_task.get('type', 'unknown')
            task_status = current_task.get('status', 'pending')

            log.info(f"[Recovery] Aktuális task: {task_id}")
            log.info(f"[Recovery] Type: {task_type}, Status: {task_status}")

            # 2. Confirm kattintás + várakozás
            self._click_confirm_and_wait()

            # 3. Állapot alapú helyreállítás
            if task_type == "gathering":
                self._recover_gathering_task(current_task, task_status)

            elif task_type == "training":
                self._recover_training_task(current_task, task_status)

            elif task_type == "alliance":
                # Alliance task egyszerűen újra queue-ba
                log.info("[Recovery] Alliance task újraindítása")
                queue_manager.requeue_task(current_task)

            else:
                # Egyéb task típus
                log.info(f"[Recovery] {task_type} task újraindítása")
                queue_manager.requeue_task(current_task)

        except Exception as e:
            log.error(f"[Recovery] Helyreállítási hiba: {e}")
            import traceback
            traceback.print_exc()

    def _recover_gathering_task(self, task, status):
        """
        Gathering task helyreállítás

        Args:
            task: Task dict
            status: Task állapot
        """
        task_id = task['task_id']
        commander = task['data'].get('commander', 'unknown')
        resource = task['data'].get('resource', 'wheat')

        if status == "sending":
            # Még nem indult el → újrakezd
            log.info(f"[Recovery] Gathering SENDING → újraindítás ({commander})")
            queue_manager.requeue_task(task)

        elif status == "marching":
            # Marching alatt → NEM tudja a gather_time-ot!
            # → DEFAULT TIMER beállítás
            log.warning(f"[Recovery] Gathering MARCHING megszakadt → default {self.default_recovery_time}sec timer ({commander})")

            timer_manager.add_timer(
                timer_id=f"gathering_{commander}_recovery",
                deadline_seconds=self.default_recovery_time,
                task_id=commander,
                task_type="gathering",
                data={"resource": resource, "recovery": True}
            )

            # Task törlése queue-ból (timer fogja kezelni)
            queue_manager.remove_task(task_id)

        elif status in ["gathering", "returning"]:
            # Timer már be van állítva → folytatás
            log.info(f"[Recovery] Gathering {status.upper()} → timer már beállítva, folytatás ({commander})")
            # Nem kell csinálni semmit

        else:
            # Ismeretlen status → újrakezd
            log.warning(f"[Recovery] Gathering ismeretlen status '{status}' → újraindítás ({commander})")
            queue_manager.requeue_task(task)

    def _recover_training_task(self, task, status):
        """
        Training task helyreállítás

        Args:
            task: Task dict
            status: Task állapot
        """
        task_id = task['task_id']
        building = task['data'].get('building', 'unknown')

        if status in ["sending", "training_setup"]:
            # Még setup fázis → újrakezd
            log.info(f"[Recovery] Training {status.upper()} → újraindítás ({building})")
            queue_manager.requeue_task(task)

        elif status in ["training_in_progress", "completed"]:
            # Training már megy vagy kész → timer már be van állítva
            log.info(f"[Recovery] Training {status.upper()} → timer már beállítva, folytatás ({building})")
            # Nem kell csinálni semmit

        else:
            # Ismeretlen status → újrakezd
            log.warning(f"[Recovery] Training ismeretlen status '{status}' → újraindítás ({building})")
            queue_manager.requeue_task(task)

    def _click_confirm_and_wait(self):
        """
        Confirm gomb kattintás + várakozás network check-kel

        Működés:
        1. Confirm gomb kattintás
        2. Várakozás (recovery_wait másodpercig)
        3. Várakozás közben 5 másodpercenként ellenőrzi a network disconnect-et
        4. Ha újra feljön → confirm + RESTART a várakozás
        """
        if not self.confirm_button:
            log.error("[Recovery] Confirm button nincs beállítva!")
            return

        log.info("[Recovery] Confirm gomb kattintás...")

        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"[Recovery] Várakozás {delay:.1f} mp")
        time.sleep(delay)

        safe_click(self.confirm_button)

        log.wait(f"[Recovery] Várakozás {self.recovery_wait} másodperc (network check 5 mp-enként)...")

        # Várakozás network check-kel
        elapsed = 0
        check_interval = 5  # 5 másodpercenként ellenőrzés

        while elapsed < self.recovery_wait:
            # Várakozás 5 másodpercig (vagy ami még hátravan)
            wait_time = min(check_interval, self.recovery_wait - elapsed)
            time.sleep(wait_time)
            elapsed += wait_time

            # Network check
            if self._check_connection_lost():
                log.warning(f"[Recovery] Network disconnect ÚJRA észlelve {elapsed}s után!")
                log.info("[Recovery] Confirm gomb újra kattintás...")

                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"[Recovery] Várakozás {delay:.1f} mp")
                time.sleep(delay)

                safe_click(self.confirm_button)

                log.info(f"[Recovery] Várakozás ÚJRAINDÍTVA ({self.recovery_wait} sec)")
                elapsed = 0  # RESTART a várakozás

        log.success("[Recovery] Helyreállítás befejezve")


# Globális singleton instance
connection_monitor = ConnectionMonitor()
