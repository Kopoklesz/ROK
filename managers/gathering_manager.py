"""
ROK Auto Farm - Gathering Manager
Commander-based gathering manager

MÓDOSÍTÁSOK (2025-12-14):
1. March.png detekció Search button után → bezárás + 5 perc retry
2. Gather button fail → progressive retry (5/15/30 perc)
3. March Time OCR → Konszenzus alapú (3 olvasás), default 5 perc ha sikertelen
4. Gather Time validáció → max 8h (ROK max), default 3 óra ha sikertelen
   - 60 próba retry, majd commander elküldése 3 óra idővel
"""
import time
import json
import threading
from pathlib import Path

from library import (
    safe_click, press_key, wait_random, get_screen_center,
    ImageManager
)
from utils.logger import FarmLogger as log
from utils.queue_manager import queue_manager
from utils.timer_manager import timer_manager
from utils.time_utils import format_time, parse_time
from utils.ocr_parser import parse_resource_value

# Farm típusok importálása
import sys
sys.path.append(str(Path(__file__).parent.parent))

from farms.wheat_farm import WheatFarm
from farms.wood_farm import WoodFarm
from farms.stone_farm import StoneFarm
from farms.gold_farm import GoldFarm


class GatheringManager:
    """Gathering Manager - Commander koordináció"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / 'config'
        self.images_dir = Path(__file__).parent.parent / 'images'
        
        # Settings betöltése
        settings_file = self.config_dir / 'settings.json'
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Gathering config
        gathering_config = settings.get('gathering', {})
        self.max_commanders = gathering_config.get('max_commanders', 5)
        self.commanders = gathering_config.get('commanders', [])
        
        # Human wait
        human_wait = settings.get('human_wait', {})
        self.human_wait_min = human_wait.get('min_seconds', 5)
        self.human_wait_max = human_wait.get('max_seconds', 10)
        
        # Defaults
        defaults = settings.get('defaults', {})
        self.default_march_time = defaults.get('march_time_seconds', 300)
        self.default_gather_time = defaults.get('gather_time_seconds', 5400)

        # OCR/Detection failure counters (védekezés az éjszakai OCR hibák ellen)
        self.gather_time_failure_count = {}  # {commander_id: count}
        self.gather_button_failure_count = {}  # {commander_id: count}

        # Farm típusok
        self.farms = {
            'wheat': WheatFarm(),
            'wood': WoodFarm(),
            'stone': StoneFarm(),
            'gold': GoldFarm()
        }
        
        self.selected_resource = None
        
        # ÚJ: March detection region betöltése
        gathering_coords_file = self.config_dir / 'gathering_coords.json'
        if gathering_coords_file.exists():
            with open(gathering_coords_file, 'r', encoding='utf-8') as f:
                gathering_coords_config = json.load(f)
                self.march_detection_region = gathering_coords_config.get('march_detection_region')
        else:
            self.march_detection_region = None
        
        self.running = False
    
    def start(self):
        """Gathering Manager indítás - Első commanders start"""
        if self.running:
            log.warning("[Gathering] Manager már fut!")
            return
        
        log.separator('=', 60)
        log.info("[Gathering] 🌾 COMMANDERS ELSŐ INDÍTÁSA")
        log.separator('=', 60)

        # Minden enabled commander queue-ba (erőforrás OCR csak a farm ciklusban lesz)
        for commander_config in self.commanders:
            commander_id = commander_config.get('id', 0)
            enabled = commander_config.get('enabled', False)
            
            if not enabled:
                log.info(f"[Gathering] Commander #{commander_id} disabled, skip")
                continue
            
            log.info(f"[Gathering] Commander #{commander_id} queue-ba helyezése...")
            
            task_id = f"commander_{commander_id}_start"
            queue_manager.add_task(task_id, "gathering", data={'commander_id': commander_id})
            
            log.success(f"[Gathering] Commander #{commander_id} queue-ba téve (start)")
        
        enabled_count = sum(1 for c in self.commanders if c.get('enabled', False))
        disabled_count = len(self.commanders) - enabled_count
        
        log.separator('-', 60)
        log.success(f"[Gathering] {enabled_count} commander queue-ba téve, {disabled_count} disabled")
        log.separator('=', 60)
        
        self.running = True
    
    def stop(self):
        """Gathering Manager leállítás"""
        if not self.running:
            return
        
        self.running = False
        log.info("[Gathering] Manager leállítva")
    
    def _select_lowest_resource(self):
        """Erőforrások kiolvasása + legkevesebb választása"""
        log.info("[Gathering] Erőforrások kiolvasása...")

        # Resource regions betöltése (FIX: resource_regions.json → farm_regions.json)
        resource_regions_file = self.config_dir / 'farm_regions.json'
        if not resource_regions_file.exists():
            log.warning("[Gathering] farm_regions.json nem található, default: wheat")
            self.selected_resource = 'wheat'
            return
        
        with open(resource_regions_file, 'r', encoding='utf-8') as f:
            resource_regions = json.load(f)
        
        resources = {}
        
        # OCR minden erőforrásra
        for resource_type in ['wheat', 'wood', 'stone', 'gold']:
            region = resource_regions.get(resource_type)
            
            if not region:
                continue
            
            log.ocr(f"[Gathering] {resource_type.upper()} OCR → Region: (x:{region.get('x',0)}, y:{region.get('y',0)}, w:{region.get('width',0)}, h:{region.get('height',0)})")

            # Javított OCR preprocessing használata
            ocr_text = ImageManager.read_text_from_region(region, debug_save=False)

            if not ocr_text:
                log.warning(f"[Gathering] {resource_type.upper()} OCR üres, skip")
                continue
            
            log.info(f"[Gathering] {resource_type.upper()} OCR nyers: '{ocr_text}'")
            
            value = parse_resource_value(ocr_text)
            
            if value > 0:
                resources[resource_type] = value
                log.success(f"[Gathering] {resource_type.upper()}: {ocr_text} → {value:,}")
            else:
                log.warning(f"[Gathering] {resource_type.upper()} parse hiba, skip")
        
        if not resources:
            log.warning("[Gathering] Egyik erőforrás sem olvasható, default: wheat")
            self.selected_resource = 'wheat'
            return
        
        # Osztás + legkisebb kiválasztása
        divisors = {'wheat': 4, 'wood': 4, 'stone': 3, 'gold': 2}
        
        adjusted = {}
        for resource_type, value in resources.items():
            divisor = divisors.get(resource_type, 1)
            adjusted[resource_type] = value / divisor
            log.info(f"[Gathering] {resource_type.upper()} adjusted: {value:,} ÷ {divisor} = {adjusted[resource_type]:.0f}")
        
        self.selected_resource = min(adjusted, key=adjusted.get)
        log.success(f"[Gathering] Kiválasztva: {self.selected_resource.upper()}")
    
    def run_commander(self, commander_id, task_data):
        """
        Commander gathering futtatás
        
        Args:
            commander_id: Commander ID (1-5)
            task_data: Task data
        """
        log.separator('=', 60)
        log.info(f"[Gathering] 🌾 COMMANDER #{commander_id} - GATHERING START")
        log.separator('=', 60)
        
        log.info(f"[Gathering] Commander #{commander_id} indítása...")
        
        # Farm ciklus futtatása
        result = self._run_single_farm(commander_id, task_data)
        
        if result == "RETRY_LATER":
            log.info(f"[Gathering] Commander #{commander_id} retry később")
            log.separator('=', 60)
            return
        
        if result == "RESTART":
            log.error(f"[Gathering] Commander #{commander_id} HIBA")
            log.separator('=', 60)
            return
        
        # Sikeres: march_time + gather_time
        march_time = result.get('march_time', 0)
        gather_time = result.get('gather_time', 0)
        total_time = march_time + gather_time
        
        # Timer beállítás
        log.info(f"[Gathering] Commander #{commander_id} - March time: {format_time(march_time)} ({march_time} sec)")
        log.info(f"[Gathering] Commander #{commander_id} - Gather time: {format_time(gather_time)} ({gather_time} sec)")
        log.info(f"[Gathering] Commander #{commander_id} - Össz idő: {format_time(total_time)} ({total_time} sec)")
        
        timer_manager.add_timer(
            timer_id=f"commander_{commander_id}",
            deadline_seconds=total_time,
            task_id=f"commander_{commander_id}_restart",
            task_type="gathering",
            data=task_data
        )
        
        log.success(f"[Gathering] Commander #{commander_id} timer beállítva: {format_time(total_time)} múlva restart")
        
        log.separator('=', 60)
        log.success(f"[Gathering] Commander #{commander_id} SIKERES BEFEJEZÉS")
        log.separator('=', 60)
    
    def _run_single_farm(self, commander_id, task_data):
        """
        Egyetlen farm ciklus futtatása

        13 lépés (+ 5a march detekció):
        1. SPACE
        2. B (térkép)
        3. Resource icon
        4. Level button
        5. Search button
        5a. March.png detekció (ÚJ) ← MÓDOSÍTÁS #1
        6. Gather button + RETRY LOGIC ← MÓDOSÍTÁS #2
        7. New troops
        8. March Time OCR (konszenzus)
        9. March button
        10. Várakozás (march + 1 sec)
        11. Képernyő közép
        12. Gather Time OCR + VALIDÁCIÓ ← MÓDOSÍTÁS #3
        13. SPACE
        """
        try:
            farm = self.farms.get(self.selected_resource)
            
            log.info(f"[Gathering] Step 1/5: Resource OCR")
            log.separator('-', 60)
            log.info(f"[Gathering] 📊 ERŐFORRÁSOK KIOLVASÁSA")
            log.separator('-', 60)
            
            # Erőforrások újraolvasása
            self._select_lowest_resource()
            farm = self.farms.get(self.selected_resource)
            
            log.info(f"[Gathering] Step 2/5: Térkép navigáció")
            log.separator('-', 60)
            log.info(f"[Gathering] 🗺️ TÉRKÉP MEGNYITÁSA")
            log.separator('-', 60)
            
            # 1. SPACE
            log.info(f"[Gathering] [1/13] SPACE billentyű")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("[Gathering] SPACE lenyomása")
            press_key('space')
            log.success(f"[Gathering] SPACE OK")
            
            # 2. B (térkép)
            log.info(f"[Gathering] [2/13] B billentyű (térkép)")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("[Gathering] B billentyű lenyomása")
            press_key('b')
            log.success(f"[Gathering] B OK")
            
            log.info(f"[Gathering] Step 3/5: Farm keresés")
            log.separator('-', 60)
            log.info(f"[Gathering] 🔍 {self.selected_resource.upper()} FARM KERESÉS")
            log.separator('-', 60)
            
            # 3. Resource icon
            log.info(f"[Gathering] [3/13] Resource icon kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('resource_icon', [0, 0])
            log.click(f"[Gathering] {farm.farm_type.upper()} ikon → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] Resource icon OK")
            
            # 4. Level button
            log.info(f"[Gathering] [4/13] Level button kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('level_button', [0, 0])
            log.click(f"[Gathering] Szint gomb → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] Level button OK")
            
            # 5. Search button
            log.info(f"[Gathering] [5/13] Search button kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('search_button', [0, 0])
            log.click(f"[Gathering] Keresés gomb → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] Search button OK")
            
            # ===== ÚJ: 5a. March.png detekció (MÓDOSÍTÁS #1) =====
            log.info(f"[Gathering] [5a/13] March.png detekció")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            time.sleep(delay)
            
            march_template = self.images_dir / 'march.png'
            
            if march_template.exists() and self.march_detection_region:
                log.search(f"[Gathering] march.png keresés...")
                
                region = self.march_detection_region
                log.info(f"[Gathering] Keresés régióban: (x:{region['x']}, y:{region['y']}, w:{region['width']}, h:{region['height']})")
                
                # Screenshot a régióból
                from PIL import ImageGrab
                import cv2
                import numpy as np
                
                x, y, w, h = region['x'], region['y'], region['width'], region['height']
                region_img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                
                # Template matching
                region_np = cv2.cvtColor(np.array(region_img), cv2.COLOR_RGB2BGR)
                template = cv2.imread(str(march_template))
                
                if template is not None:
                    result = cv2.matchTemplate(region_np, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val >= 0.7:
                        match_x = x + max_loc[0] + template.shape[1] // 2
                        match_y = y + max_loc[1] + template.shape[0] // 2
                        
                        log.warning(f"[Gathering] march.png megtalálva régióban → ({match_x}, {match_y})")
                        log.warning("[Gathering] Commander már úton van!")
                        log.info("[Gathering] Visszalépés és 5 perc retry")

                        # Képernyő közép kattintás (bezárás)
                        delay = wait_random(self.human_wait_min, self.human_wait_max)
                        log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
                        time.sleep(delay)

                        screen_center = get_screen_center()
                        log.click(f"[Gathering] Képernyő közép → {screen_center}")
                        safe_click(screen_center)
                        time.sleep(1)
                        
                        # SPACE
                        log.action("[Gathering] SPACE lenyomása")
                        press_key('space')
                        
                        # 5 perc múlva újra
                        timer_manager.add_timer(
                            timer_id=f"commander_{commander_id}_march_retry",
                            deadline_seconds=300,
                            task_id=f"commander_{commander_id}_restart",
                            task_type="gathering",
                            data=task_data
                        )
                        
                        log.success(f"[Gathering] Commander #{commander_id} retry: 5 perc múlva")
                        return "RETRY_LATER"
                    else:
                        log.success("[Gathering] march.png nem található régióban - commander elérhető")
            
            log.info(f"[Gathering] Step 4/5: Farm process")
            log.separator('-', 60)
            log.info(f"[Gathering] 🎯 GATHERING INDÍTÁS")
            log.separator('-', 60)
            
            # ===== 6. Gather button (MÓDOSÍTÁS #2) =====
            log.info(f"[Gathering] [6/13] Gather button keresés")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            
            log.search(f"[Gathering] gather.png keresés...")
            gather_coords = farm.find_gather_button()
            
            if not gather_coords:
                # Gather button nem található → progressive retry
                if commander_id not in self.gather_button_failure_count:
                    self.gather_button_failure_count[commander_id] = 0

                self.gather_button_failure_count[commander_id] += 1
                failure_count = self.gather_button_failure_count[commander_id]

                log.error(f"[Gathering] Gather gomb nem található! ({failure_count}x)")
                log.warning("[Gathering] Commander valószínűleg még úton van VAGY rossz képernyő")

                # Progressive retry időzítés:
                # 1-2. hiba: 5 perc (várhatóan commander march time)
                # 3-4. hiba: 15 perc (lehet stuck)
                # 5+. hiba: 30 perc (valószínűleg hiba van)
                if failure_count <= 2:
                    retry_seconds = 300  # 5 perc
                elif failure_count <= 4:
                    retry_seconds = 900  # 15 perc
                else:
                    retry_seconds = 1800  # 30 perc

                log.info(f"[Gathering] Task visszatéve queue-ba {retry_seconds//60} perc múlvára")

                # Bezárás (2x SPACE = clean state)
                delay = wait_random(self.human_wait_min, self.human_wait_max)
                log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
                time.sleep(delay)

                log.action("[Gathering] SPACE #1 lenyomása (kigugrás)")
                press_key('space')
                time.sleep(1.0)
                log.action("[Gathering] SPACE #2 lenyomása (városba vissza)")
                press_key('space')
                log.info("[Gathering] 2x SPACE → clean state (városban, minden bezárva)")

                # Progressive retry
                timer_manager.add_timer(
                    timer_id=f"commander_{commander_id}_gather_retry",
                    deadline_seconds=retry_seconds,
                    task_id=f"commander_{commander_id}_restart",
                    task_type="gathering",
                    data=task_data
                )

                log.success(f"[Gathering] Commander #{commander_id} retry: {retry_seconds//60} perc múlva")
                return "RETRY_LATER"

            # Sikeres gather button detection → failure counter reset
            self.gather_button_failure_count[commander_id] = 0
            log.success(f"[Gathering] Gather gomb megtalálva → {gather_coords}")

            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)

            log.click(f"[Gathering] Gather gomb kattintás")
            safe_click(gather_coords)
            log.success(f"[Gathering] Gather button OK")
            
            # 7. New troops
            log.info(f"[Gathering] [7/13] New troops kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('new_troops', [0, 0])
            log.click(f"[Gathering] New troops → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] New troops OK")
            
            # 8. March Time OCR (konszenzus alapú, mint training manager)
            log.info(f"[Gathering] [8/13] March Time OCR (konszenzus)")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)

            log.ocr(f"[Gathering] March Time kiolvasása (konszenzus)...")
            # Konszenzus: 3 OCR olvasás
            from collections import Counter
            march_readings = []
            for sub_attempt in range(3):
                if sub_attempt > 0:
                    time.sleep(0.2)
                temp_march = farm.read_time('march_time', debug_save=False)
                if temp_march:
                    march_readings.append(temp_march)

            if march_readings:
                march_counter = Counter(march_readings)
                march_time, votes = march_counter.most_common(1)[0]
                log.success(f"[Gathering] March Time konszenzus ({votes}/{len(march_readings)}): {format_time(march_time)} ({march_time} sec)")
            else:
                march_time = 300  # Default 5 perc
                log.warning(f"[Gathering] March Time OCR hiba! Default: 5 perc (300 sec)")

            # 9. March button
            log.info(f"[Gathering] [9/13] March button kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            coords = farm.coords.get('march_button', [0, 0])
            log.click(f"[Gathering] March gomb → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] March button OK")
            
            # 10. Várakozás (march + 1 sec) + Alliance help közben
            log.info(f"[Gathering] [10/13] Várakozás march time + 1 sec (alliance help check közben)")
            wait_duration = march_time + 1
            log.wait(f"[Gathering] Várakozás {wait_duration} sec (march time + 1, alliance help check minden 5 sec)")

            # Marching wait alliance help check-kel
            self._wait_with_alliance_help_check(wait_duration)

            log.success(f"[Gathering] Várakozás OK")

            # 11. Képernyő közepe
            log.info(f"[Gathering] [11/13] Képernyő közép kattintás")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            screen_center = get_screen_center()
            coords = farm.coords.get('screen_center', screen_center)
            log.click(f"[Gathering] Képernyő közép → {coords}")
            safe_click(coords)
            log.success(f"[Gathering] Screen center OK")

            # 12. Gather Time OCR (max 60 retry, default 3 óra ha sikertelen)
            log.info(f"[Gathering] [12/13] Gather Time OCR (max 60 retry)")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)

            gather_time = None
            for attempt in range(60):
                log.ocr(f"[Gathering] Gather Time kiolvasás (kísérlet {attempt+1}/60)...")
                # Debug screenshot minden 5. próbálkozásnál
                debug_save = ((attempt + 1) % 5 == 0)
                temp_time = farm.read_time('gather_time', debug_save=debug_save)

                # VALIDÁCIÓ: max 8 óra (28800 sec) - ROK max gather time
                if temp_time and temp_time <= 28800:
                    gather_time = temp_time
                    # Sikeres OCR → failure counter reset
                    self.gather_time_failure_count[commander_id] = 0
                    log.success(f"[Gathering] Gather Time: {format_time(gather_time)} ({gather_time} sec) - {attempt+1}. próba")
                    break
                elif temp_time and temp_time > 28800:
                    log.warning(f"[Gathering] Gather Time túl nagy: {format_time(temp_time)} > 8h, retry...")

                if (attempt + 1) % 10 == 0:
                    log.warning(f"[Gathering] Gather Time OCR hiba ({attempt+1}/60), retry...")

                time.sleep(1.0)

            if gather_time is None:
                # OCR sikertelen → default 3 óra (10800 sec) és újrapróbálás
                gather_time = 10800  # 3 óra default
                log.warning(f"[Gathering] ⚠️ Gather Time OCR 60 próba után sikertelen!")
                log.warning(f"[Gathering] ⚠️ Default 3 óra (10800 sec) beállítva, commander elküldve")
                log.warning(f"[Gathering] ⚠️ 3 óra múlva újra megpróbálja...")

            # 13. SPACE (bezárás)
            log.info(f"[Gathering] [13/13] SPACE (bezárás)")
            delay = wait_random(self.human_wait_min, self.human_wait_max)
            log.wait(f"[Gathering] Várakozás {delay:.1f} mp")
            time.sleep(delay)
            log.action("[Gathering] SPACE lenyomása")
            press_key('space')
            log.success(f"[Gathering] SPACE OK")

            log.separator('-', 60)
            log.success(f"[Gathering] Farm ciklus befejezve: March={format_time(march_time)}, Gather={format_time(gather_time)}")
            log.separator('-', 60)
            
            log.success(f"[Gathering] Farm process OK")
            
            log.info(f"[Gathering] Step 5/5: Timer beállítása")
            
            return {
                'march_time': march_time,
                'gather_time': gather_time
            }
        
        except Exception as e:
            log.error(f"[Gathering] Farm ciklus HIBA: {e}")
            import traceback
            traceback.print_exc()
            return "RESTART"

    def _wait_with_alliance_help_check(self, wait_duration):
        """
        Várakozás alliance help check-kel

        Marching közben 5 másodpercenként ellenőrzi az alliance hand png-t
        az 1-es pozícióban. Ha megtalálja → kattintás.

        Args:
            wait_duration: Várakozási idő (másodperc)
        """
        from managers.alliance_manager import alliance_manager

        elapsed = 0
        check_interval = 5  # 5 másodpercenként ellenőrzés

        hand_template = self.images_dir / 'hand.png'
        hand_locations = self._load_alliance_coords().get('hand_locations', [])

        while elapsed < wait_duration:
            # Várakozás 5 másodpercig (vagy ami még hátravan)
            wait_time = min(check_interval, wait_duration - elapsed)
            time.sleep(wait_time)
            elapsed += wait_time

            # Alliance help check (csak az 1-es pozíció)
            if hand_locations and len(hand_locations) > 0:
                location_1 = hand_locations[0]
                x, y = location_1.get('x', 0), location_1.get('y', 0)

                log.info(f"[Gathering] Alliance help check (marching közben, {elapsed}s / {wait_duration}s)")

                # Template matching az 1-es pozícióban
                if hand_template.exists():
                    # Kicsi régió az 1-es pozíció körül (pl. 100x100 px)
                    # ImageManager.find_image használata (nincs find_image_in_region!)
                    # Teljes képernyőn keres, de az eredményt ellenőrizzük hogy a régióban van-e
                    coords = ImageManager.find_image(str(hand_template), threshold=0.6)

                    # Ellenőrzés: a koordináta a fix pont körüli régióban van-e?
                    if coords:
                        region_x_min = max(0, x - 50)
                        region_y_min = max(0, y - 50)
                        region_x_max = x + 50
                        region_y_max = y + 50

                        found_x, found_y = coords
                        if not (region_x_min <= found_x <= region_x_max and region_y_min <= found_y <= region_y_max):
                            # Kívül esik a régión
                            coords = None

                    if coords:
                        log.success(f"[Gathering] Alliance hand MEGTALÁLVA marching közben → {coords}")

                        delay = wait_random(self.human_wait_min, self.human_wait_max)
                        log.wait(f"[Gathering] Várakozás {delay:.1f} mp (alliance help)")
                        time.sleep(delay)

                        log.click(f"[Gathering] Alliance help kattintás (marching közben) → {coords}")
                        safe_click(coords)
                        log.success("[Gathering] Alliance help OK (marching közben)")
                    else:
                        log.info("[Gathering] Alliance hand nem található (marching közben)")

        log.info(f"[Gathering] Marching wait befejezve ({wait_duration}s)")

    def _load_alliance_coords(self):
        """Alliance coords betöltése"""
        coords_file = self.config_dir / 'alliance_coords.json'
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}


# Globális singleton instance
gathering_manager = GatheringManager()