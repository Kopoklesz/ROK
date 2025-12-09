"""
ROK Auto Farm - Training Manager
ÚJ VERZIÓ (1.1.0):
- Panel-alapú OCR rendszer
- Mind a 4 egység időt beolvassa egyszerre
- "completed" és "idle" státusz kezelés
- Gather troops opcionális (idle esetén kihagyva)
"""
import time
import json
import re
from pathlib import Path

from library import safe_click, press_key, wait_random
from utils.logger import FarmLogger as log
from utils.queue_manager import queue_manager
from utils.timer_manager import timer_manager
from utils.time_utils import parse_time, format_time
from library import ImageManager


class TrainingManager:
    """Training Manager - Katonák kiképzése panel OCR-rel"""

    # Building nevek sorrendben
    BUILDINGS = ['barracks', 'archery', 'stable', 'siege']

    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / 'config'

        # Settings betöltése
        settings_file = self.config_dir / 'settings.json'
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)

        # Training config
        training_config = settings.get('training', {})
        self.buildings = training_config.get('buildings', {})

        # Human wait (training gyorsabb: 2-6 sec)
        self.human_wait_min = 2
        self.human_wait_max = 6

        # Training time régiók
        time_regions_file = self.config_dir / 'training_time_regions.json'
        if time_regions_file.exists():
            with open(time_regions_file, 'r', encoding='utf-8') as f:
                self.time_regions = json.load(f)
        else:
            self.time_regions = {}

        # Training koordináták
        training_coords_file = self.config_dir / 'training_coords.json'
        if training_coords_file.exists():
            with open(training_coords_file, 'r', encoding='utf-8') as f:
                self.training_coords = json.load(f)
        else:
            self.training_coords = {}

        self.running = False
    
    def start(self):
        """
        Training Manager indítás

        Új folyamat:
        1. Panel megnyitása
        2. Mind a 4 egység OCR
        3. Panel bezárása
        4. Queue-ba rakás
        """
        if self.running:
            log.warning("[Training] Manager már fut!")
            return

        log.separator('=', 60)
        log.info("[Training] Manager indítás...")
        log.separator('=', 60)

        # Panel OCR check (induláskor)
        self._scan_training_panel()

        log.separator('=', 60)
        log.success("[Training] Manager inicializálva")
        log.separator('=', 60)

        self.running = True

    def stop(self):
        """Training Manager leállítás"""
        if not self.running:
            return

        self.running = False

        log.info("[Training] Manager leállítva")
    
    def _scan_training_panel(self):
        """
        Panel OCR folyamat (START / check_after_upgrade esetén):
        1. Panel megnyitása (queue menü)
        2. Mind a 4 épület ellenőrzése (_check_and_process_building)
        3. Ha restart szükséges → queue bezárás, training, queue ÚJRA megnyitás
        4. Panel bezárása
        """
        log.info("[Training] Panel OCR indítása...")

        open_panel_coords = self.training_coords.get('open_panel', [0, 0])
        close_panel_coords = self.training_coords.get('close_panel', [0, 0])

        if open_panel_coords == [0, 0] or close_panel_coords == [0, 0]:
            log.error("[Training] Panel koordináták nincsenek beállítva!")
            return

        queue_open = False

        try:
            # 1. Queue menü megnyitása
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)

            log.click(f"[Training] PANEL MEGNYITÁS → {open_panel_coords}")
            safe_click(open_panel_coords)
            queue_open = True
            log.success("[Training] Panel megnyitva")

            # 2. Mind a 4 épület ellenőrzése
            for building_name in self.BUILDINGS:
                # Ellenőrzés: enabled-e
                building_config = self.buildings.get(building_name, {})
                enabled = building_config.get('enabled', True)

                if not enabled:
                    log.info(f"[Training] {building_name.upper()}: Disabled, skip")
                    continue

                # Épület ellenőrzés
                result = self._check_and_process_building(building_name)

                # Ha restart szükséges
                if result['action'] == 'restart_needed':
                    # Queue menü bezárása
                    delay = wait_random(self.human_wait_min, self.human_wait_max)
                    log.wait(f"[Training] Várakozás {delay:.1f} mp")
                    time.sleep(delay)

                    log.click(f"[Training] PANEL BEZÁRÁS → {close_panel_coords}")
                    safe_click(close_panel_coords)
                    queue_open = False
                    log.success("[Training] Panel bezárva")

                    # Training végrehajtás
                    self._execute_training(building_name, result['skip_gather'])

                    # Queue menü ÚJRA megnyitása (következő épülethez)
                    delay = wait_random(self.human_wait_min, self.human_wait_max)
                    log.wait(f"[Training] Várakozás {delay:.1f} mp")
                    time.sleep(delay)

                    log.click(f"[Training] PANEL ÚJRA MEGNYITÁS → {open_panel_coords}")
                    safe_click(open_panel_coords)
                    queue_open = True
                    log.success("[Training] Panel újra megnyitva")

        finally:
            # Panel bezárása (ha még nyitva)
            if queue_open:
                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"[Training] Várakozás {delay:.1f} mp")
                time.sleep(delay)

                log.click(f"[Training] PANEL BEZÁRÁS → {close_panel_coords}")
                safe_click(close_panel_coords)
                log.success("[Training] Panel bezárva")

    def _is_building_upgrading(self, building_name):
        """
        Ellenőrzi hogy EZ AZ EGY épület upgrade alatt van-e

        Feltételezi: Upgrade menü NYITVA van

        Mindkét slot-ot ellenőrzi:
        - upgrade_name_region_1 OCR → ha match → upgrade_time_region_1 OCR
        - upgrade_name_region_2 OCR → ha match → upgrade_time_region_2 OCR

        Args:
            building_name: Building név (barracks, archery, stable, siege)

        Returns:
            tuple: (is_upgrading: bool, upgrade_time_sec: int or None)
        """
        building_names = {
            'barracks': 'barracks',
            'archery': 'archery range',
            'stable': 'stable',
            'siege': 'siege workshop'
        }

        search_name = building_names.get(building_name, building_name)

        # Régió 1 ellenőrzés
        region_1 = self.time_regions.get('upgrade_name_region_1')
        if region_1 and region_1.get('x', 0) != 0:
            log.ocr(f"[Training] {building_name.upper()} upgrade check → Region 1")
            ocr_text_1 = ImageManager.read_text_from_region(region_1)
            if ocr_text_1:
                log.info(f"[Training] Upgrade Region 1 OCR: '{ocr_text_1}'")
                if search_name.lower() in ocr_text_1.lower():
                    log.warning(f"[Training] {building_name.upper()} UPGRADING (Region 1)!")
                    # Upgrade time beolvasása region_1-ből
                    time_region_1 = self.time_regions.get('upgrade_time_region_1')
                    if time_region_1 and time_region_1.get('x', 0) != 0:
                        upgrade_time = self._read_upgrade_time_from_region(time_region_1, building_name, "Region 1")
                        return (True, upgrade_time)
                    else:
                        # Fallback: 2 óra
                        return (True, 7200)

        # Régió 2 ellenőrzés
        region_2 = self.time_regions.get('upgrade_name_region_2')
        if region_2 and region_2.get('x', 0) != 0:
            log.ocr(f"[Training] {building_name.upper()} upgrade check → Region 2")
            ocr_text_2 = ImageManager.read_text_from_region(region_2)
            if ocr_text_2:
                log.info(f"[Training] Upgrade Region 2 OCR: '{ocr_text_2}'")
                if search_name.lower() in ocr_text_2.lower():
                    log.warning(f"[Training] {building_name.upper()} UPGRADING (Region 2)!")
                    # Upgrade time beolvasása region_2-ből
                    time_region_2 = self.time_regions.get('upgrade_time_region_2')
                    if time_region_2 and time_region_2.get('x', 0) != 0:
                        upgrade_time = self._read_upgrade_time_from_region(time_region_2, building_name, "Region 2")
                        return (True, upgrade_time)
                    else:
                        # Fallback: 2 óra
                        return (True, 7200)

        # Nem található upgrade
        log.info(f"[Training] {building_name.upper()} NEM upgrading")
        return (False, None)

    def _read_upgrade_time_from_region(self, region, building_name, region_name, max_attempts=5):
        """
        Upgrade time beolvasása egy adott régióból

        Args:
            region: dict - OCR régió
            building_name: str
            region_name: str - log-hoz
            max_attempts: int

        Returns:
            int: upgrade time másodpercben (fallback: 7200)
        """
        log.ocr(f"[Training] {building_name.upper()} UPGRADE TIME OCR → {region_name}")

        for attempt in range(1, max_attempts + 1):
            ocr_text = ImageManager.read_text_from_region(region)

            if not ocr_text:
                time.sleep(0.5)
                continue

            log.info(f"[Training] {building_name.upper()} UPGRADE TIME ({region_name}, kísérlet {attempt}): '{ocr_text}'")

            # Parse time
            time_sec = parse_time(ocr_text)
            # Upgrade time mindig >0 kell legyen (nem lehet idle vagy completed)
            if time_sec is not None and time_sec > 0:
                log.success(f"[Training] {building_name.upper()} → UPGRADE TIME: {format_time(time_sec)} ({time_sec} sec)")
                return time_sec

            time.sleep(0.5)

        log.warning(f"[Training] {building_name.upper()} UPGRADE TIME OCR sikertelen → fallback 2 óra")
        return 7200

    def _read_training_status(self, building_name, max_attempts=5):
        """
        Egy building státuszának beolvasása (idő / completed / idle)

        Args:
            building_name: Building név (barracks, archery, stable, siege)
            max_attempts: Max próbálkozások

        Returns:
            dict: {'type': 'time'/'completed'/'idle', 'value': seconds/None}
        """
        region_key = f"{building_name}_time"
        region = self.time_regions.get(region_key)

        if not region:
            log.warning(f"[Training] {building_name.upper()} time region nincs beállítva!")
            return {'type': 'unknown', 'value': None}

        log.ocr(f"[Training] {building_name.upper()} OCR → Region: (x:{region.get('x',0)}, y:{region.get('y',0)}, w:{region.get('width',0)}, h:{region.get('height',0)})")

        for attempt in range(1, max_attempts + 1):
            ocr_text = ImageManager.read_text_from_region(region)

            if not ocr_text:
                time.sleep(0.5)
                continue

            log.info(f"[Training] {building_name.upper()} OCR nyers szöveg (kísérlet {attempt}): '{ocr_text}'")

            # Ellenőrzés: completed?
            if re.search(r'completed', ocr_text.lower()):
                log.success(f"[Training] {building_name.upper()} → COMPLETED")
                return {'type': 'completed', 'value': None}

            # Próbáljuk parse-olni időként
            # parse_time() visszatérési értékei:
            # - None: idle állapot
            # - 0: completed állapot
            # - >0: idő másodpercben
            time_sec = parse_time(ocr_text)

            # None = idle
            if time_sec is None:
                log.success(f"[Training] {building_name.upper()} → IDLE (OCR: '{ocr_text}')")
                return {'type': 'idle', 'value': None}

            # 0 = completed
            if time_sec == 0:
                log.success(f"[Training] {building_name.upper()} → COMPLETED (OCR: '{ocr_text}')")
                return {'type': 'completed', 'value': 0}

            # >0 = time
            if time_sec > 0:
                log.success(f"[Training] {building_name.upper()} → TIME: {format_time(time_sec)} ({time_sec} sec)")
                return {'type': 'time', 'value': time_sec}

            time.sleep(0.5)

        log.warning(f"[Training] {building_name.upper()} OCR sikertelen {max_attempts} próba után!")
        return {'type': 'unknown', 'value': None}

    def _check_and_process_building(self, building_name):
        """
        Egy épület teljes ellenőrzése és feldolgozása

        Feltételezi: Queue menü NYITVA van

        Args:
            building_name: str (barracks, archery, stable, siege)

        Returns:
            dict: {
                'action': 'timer_set' / 'restart_needed' / 'done',
                'skip_gather': bool (ha action='restart_needed'),
                'upgraded_checked': bool
            }
        """
        log.info(f"[Training] {building_name.upper()} ellenőrzése...")

        # 1. Épület time OCR
        result = self._read_training_status(building_name)
        result_type = result.get('type')
        result_value = result.get('value')

        # 2. Ha IDŐ → timer beállítás
        if result_type == 'time':
            log.info(f"[Training] {building_name.upper()}: Training fut → timer {format_time(result_value)}")

            # Timer beállítása (duplikáció elkerülése: remove előbb)
            timer_id = f"training_{building_name}"
            timer_manager.remove_timer(timer_id)
            timer_manager.add_timer(
                timer_id=timer_id,
                deadline_seconds=result_value,
                task_id=f"{building_name}_restart",
                task_type="training",
                data={"building": building_name}
            )

            return {'action': 'timer_set', 'skip_gather': False, 'upgraded_checked': False}

        # 3. Ha IDLE → upgrade check
        elif result_type == 'idle':
            log.info(f"[Training] {building_name.upper()}: IDLE → upgrade check")

            # Upgrade menü megnyitása
            upgrade_check_coords = self.training_coords.get('upgrade_check_button', [0, 0])
            if upgrade_check_coords != [0, 0]:
                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"[Training] Várakozás {delay:.1f} mp")
                time.sleep(delay)

                log.click(f"[Training] UPGRADE MENÜ megnyitás → {upgrade_check_coords}")
                safe_click(upgrade_check_coords)

            # Upgrade check
            is_upgrading, upgrade_time = self._is_building_upgrading(building_name)

            # Upgrade menü bezárása
            if upgrade_check_coords != [0, 0]:
                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"[Training] Várakozás {delay:.1f} mp")
                time.sleep(delay)

                log.click(f"[Training] UPGRADE MENÜ bezárás → {upgrade_check_coords}")
                safe_click(upgrade_check_coords)

            # Ha upgrading → timer
            if is_upgrading:
                log.warning(f"[Training] {building_name.upper()}: UPGRADING → timer {format_time(upgrade_time)}")

                timer_id = f"training_{building_name}_upgrade"
                timer_manager.remove_timer(timer_id)
                timer_manager.add_timer(
                    timer_id=timer_id,
                    deadline_seconds=upgrade_time,
                    task_id=f"{building_name}_upgrade_check",
                    task_type="training",
                    data={"building": building_name, "check_after_upgrade": True}
                )

                return {'action': 'timer_set', 'skip_gather': False, 'upgraded_checked': True}

            # Ha NEM upgrading → restart kell (skip gather)
            else:
                log.info(f"[Training] {building_name.upper()}: NEM upgrading → restart (skip gather)")
                return {'action': 'restart_needed', 'skip_gather': True, 'upgraded_checked': True}

        # 4. Ha COMPLETED → restart kell (gather)
        elif result_type == 'completed':
            log.success(f"[Training] {building_name.upper()}: COMPLETED → restart (gather troops)")
            return {'action': 'restart_needed', 'skip_gather': False, 'upgraded_checked': False}

        # 5. Unknown → 5 perc retry
        else:
            log.warning(f"[Training] {building_name.upper()}: Ismeretlen státusz → 5 perc retry")

            timer_id = f"training_{building_name}_retry"
            timer_manager.remove_timer(timer_id)
            timer_manager.add_timer(
                timer_id=timer_id,
                deadline_seconds=300,
                task_id=f"{building_name}_restart",
                task_type="training",
                data={"building": building_name}
            )

            return {'action': 'timer_set', 'skip_gather': False, 'upgraded_checked': False}

    def _execute_training(self, building_name, skip_gather):
        """
        Training végrehajtása (koordináta kattintások + OCR frissítés)

        Feltételezi: Összes menü BEZÁRVA van

        Args:
            building_name: str
            skip_gather: bool

        TRAINING FÁZIS:
        1. HA skip_gather = FALSE → Troop gather
        2-5. Building/Button/Tier/Confirm
        6. 2× SPACE
        7. Panel megnyitás
        8. Épület OCR + timer beállítása
        9. Panel bezárás
        """
        log.separator('=', 60)
        log.info(f"[Training] ⚔️  {building_name.upper()} TRAINING INDÍTÁS")
        if skip_gather:
            log.info("[Training] IDLE státusz → Gather troops KIHAGYVA")
        log.separator('=', 60)

        # Koordináták betöltése
        coords = self.training_coords.get(building_name, {})

        try:
            # 1. Troop Gather (CSAK ha nem skip_gather)
            if not skip_gather:
                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"[Training] Várakozás {delay:.1f} mp")
                time.sleep(delay)

                troop_gather_coords = coords.get('troop_gather', [0, 0])
                log.click(f"[Training] TROOP GATHER kattintás → {troop_gather_coords}")
                safe_click(troop_gather_coords)
                log.success("[Training] TROOP GATHER OK")
            else:
                log.info("[Training] TROOP GATHER kihagyva (idle státusz)")

            # 2. Building
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)

            building_coords = coords.get('building', [0, 0])
            log.click(f"[Training] BUILDING kattintás → {building_coords}")
            safe_click(building_coords)
            log.success("[Training] BUILDING OK")

            # 3. Button
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)

            button_coords = coords.get('button', [0, 0])
            log.click(f"[Training] BUTTON kattintás → {button_coords}")
            safe_click(button_coords)
            log.success("[Training] BUTTON OK")

            # 4. Tier
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)

            tier_coords = coords.get('tier', [0, 0])
            log.click(f"[Training] TIER kattintás → {tier_coords}")
            safe_click(tier_coords)
            log.success("[Training] TIER OK")

            # 5. Confirm
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)

            confirm_coords = coords.get('confirm', [0, 0])
            log.click(f"[Training] CONFIRM kattintás → {confirm_coords}")
            safe_click(confirm_coords)
            log.success("[Training] CONFIRM OK")

            # 6. SPACE #1
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("[Training] SPACE #1 lenyomása")
            press_key('space')
            log.success("[Training] SPACE #1 OK")

            # 7. SPACE #2
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("[Training] SPACE #2 lenyomása")
            press_key('space')
            log.success("[Training] SPACE #2 OK")

            # 8. Panel megnyitás ÚJRA
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)

            open_panel_coords = self.training_coords.get('open_panel', [0, 0])
            log.click(f"[Training] PANEL MEGNYITÁS → {open_panel_coords}")
            safe_click(open_panel_coords)
            log.success("[Training] Panel megnyitva")

            # 9. Épület OCR + timer beállítása (csak ez az 1 épület)
            log.info(f"[Training] {building_name.upper()} OCR frissítése...")
            result = self._read_training_status(building_name)

            if result.get('type') == 'time':
                time_sec = result.get('value')
                log.info(f"[Training] {building_name.upper()} új idő: {format_time(time_sec)}")

                timer_id = f"training_{building_name}"
                timer_manager.remove_timer(timer_id)
                timer_manager.add_timer(
                    timer_id=timer_id,
                    deadline_seconds=time_sec,
                    task_id=f"{building_name}_restart",
                    task_type="training",
                    data={"building": building_name}
                )
            else:
                log.warning(f"[Training] {building_name.upper()} OCR nem sikerült → 5 perc retry")
                timer_id = f"training_{building_name}_retry"
                timer_manager.remove_timer(timer_id)
                timer_manager.add_timer(
                    timer_id=timer_id,
                    deadline_seconds=300,
                    task_id=f"{building_name}_restart",
                    task_type="training",
                    data={"building": building_name}
                )

            # 10. Panel bezárás
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)

            close_panel_coords = self.training_coords.get('close_panel', [0, 0])
            log.click(f"[Training] PANEL BEZÁRÁS → {close_panel_coords}")
            safe_click(close_panel_coords)
            log.success("[Training] Panel bezárva")

            log.separator('=', 60)
            log.success(f"[Training] {building_name.upper()} training befejezve!")
            log.separator('=', 60)

        except Exception as e:
            log.error(f"[Training] {building_name.upper()} training HIBA: {e}")
            import traceback
            traceback.print_exc()

    def restart_training(self, task_data):
        """
        Training restart folyamat (ÁTÍRT VERZIÓ - upgrade check-kel)

        ELLENŐRZÉSI FÁZIS:
        1. Panel megnyitás (queue menü)
        2. Épület OCR (csak ez az 1 épület)
        3. Eredmény kiértékelés:
           - IDŐ → timer, return
           - IDLE → upgrade check, ha upgrading: timer+return, ha nem: folytatás
           - COMPLETED → folytatás
        4. Queue menü bezárás

        TRAINING FÁZIS:
        5. _execute_training() hívása

        Args:
            task_data: {
                'building': 'barracks',
                'check_after_upgrade': False/True (opcionális)
            }
        """
        building_name = task_data.get('building', 'barracks')
        check_after_upgrade = task_data.get('check_after_upgrade', False)

        # Ha upgrade után check → teljes panel scan
        if check_after_upgrade:
            log.separator('=', 60)
            log.info(f"[Training] {building_name.upper()} UPGRADE VÉGE - Teljes panel check")
            log.separator('=', 60)

            self._scan_training_panel()

            log.separator('=', 60)
            log.success(f"[Training] {building_name.upper()} upgrade check befejezve")
            log.separator('=', 60)
            return

        # ELLENŐRZÉSI FÁZIS
        log.separator('=', 60)
        log.info(f"[Training] ⚔️  {building_name.upper()} RESTART - Ellenőrzési fázis")
        log.separator('=', 60)

        open_panel_coords = self.training_coords.get('open_panel', [0, 0])
        close_panel_coords = self.training_coords.get('close_panel', [0, 0])

        if open_panel_coords == [0, 0] or close_panel_coords == [0, 0]:
            log.error("[Training] Panel koordináták nincsenek beállítva!")
            return

        queue_open = False

        try:
            # 1. Queue menü megnyitás
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Training] Várakozás {delay:.1f} mp")
            time.sleep(delay)

            log.click(f"[Training] PANEL MEGNYITÁS → {open_panel_coords}")
            safe_click(open_panel_coords)
            queue_open = True
            log.success("[Training] Panel megnyitva")

            # 2. Épület ellenőrzés (_check_and_process_building)
            result = self._check_and_process_building(building_name)

            # 3. Eredmény kiértékelés
            if result['action'] == 'timer_set':
                # Timer már be van állítva, csak bezárjuk a menüt és kilépünk
                log.info(f"[Training] {building_name.upper()}: Timer beállítva, training NEM indul")

                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"[Training] Várakozás {delay:.1f} mp")
                time.sleep(delay)

                log.click(f"[Training] PANEL BEZÁRÁS → {close_panel_coords}")
                safe_click(close_panel_coords)
                queue_open = False
                log.success("[Training] Panel bezárva")

                return

            elif result['action'] == 'restart_needed':
                # Restart kell → bezárjuk queue-t és indítjuk a training-et
                skip_gather = result['skip_gather']

                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"[Training] Várakozás {delay:.1f} mp")
                time.sleep(delay)

                log.click(f"[Training] PANEL BEZÁRÁS → {close_panel_coords}")
                safe_click(close_panel_coords)
                queue_open = False
                log.success("[Training] Panel bezárva")

                # TRAINING FÁZIS
                self._execute_training(building_name, skip_gather)

        except Exception as e:
            log.error(f"[Training] {building_name.upper()} restart HIBA: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Queue menü bezárás (ha még nyitva)
            if queue_open:
                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"[Training] Várakozás {delay:.1f} mp")
                time.sleep(delay)

                log.click(f"[Training] PANEL BEZÁRÁS → {close_panel_coords}")
                safe_click(close_panel_coords)
                log.success("[Training] Panel bezárva")


# Globális singleton instance
training_manager = TrainingManager()