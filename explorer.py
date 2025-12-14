"""
ROK Auto Farm - Explorer
Felfedezés ellenőrzés és indítás
"""
import time
import json
from pathlib import Path

from library import safe_click, press_key, wait_random, ImageManager, find_and_close_popups, is_garbage_ocr_text
from utils.logger import FarmLogger as log
from utils.ocr_parser import parse_resource_value


class Explorer:
    """Explorer - Felfedezés kezelő"""

    def __init__(self):
        self.config_dir = Path(__file__).parent / 'config'

        # Konfigurációk betöltése
        self.settings = self._load_settings()
        self.coords = self._load_coordinates()
        self.popup_regions = self._load_popup_regions()

        # Paraméterek
        self.human_wait_min = self.settings.get('human_wait_min', 3)
        self.human_wait_max = self.settings.get('human_wait_max', 8)

    def _load_settings(self):
        """Settings.json betöltése"""
        settings_file = self.config_dir / 'settings.json'
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_coordinates(self):
        """Explorer koordináták betöltése"""
        coords_file = self.config_dir / 'explorer_coords.json'
        if coords_file.exists():
            with open(coords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _load_popup_regions(self):
        """Popup keresési régiók betöltése"""
        popup_file = self.config_dir / 'popup_regions.json'
        if popup_file.exists():
            with open(popup_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def check_exploration(self):
        """
        Felfedezés ellenőrzése

        Returns:
            bool: True ha indítani kell felfedezést, False ha nem
        """
        log.separator('=', 60)
        log.info("🔍 EXPLORER - FELFEDEZÉS ELLENŐRZÉSE")
        log.separator('=', 60)

        # 1. Que menü megnyitása
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp (emberi faktor)")
        time.sleep(delay)
        coords = self.coords.get('open_queue_menu', [0, 0])
        log.click(f"Que menü megnyitása → ({coords[0]}, {coords[1]})")
        safe_click(coords)

        # 2. Que fül bezárása
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        coords = self.coords.get('close_queue_tab', [0, 0])
        log.click(f"Que fül bezárása → ({coords[0]}, {coords[1]})")
        safe_click(coords)

        # 3. Scout fül megnyitása
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        coords = self.coords.get('open_scout_tab', [0, 0])
        log.click(f"Scout fül megnyitása → ({coords[0]}, {coords[1]})")
        safe_click(coords)

        # 4. Felfedezés % kiolvasása (3 régió - frissítve!)
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)

        region1 = self.coords.get('exploration_region_1', {})
        region2 = self.coords.get('exploration_region_2', {})
        region3 = self.coords.get('exploration_region_3', {})

        log.ocr("Felfedezés % kiolvasása (3 régió)...")

        # Régió 1 kiolvasás
        if region1:
            log.ocr(f"Régió 1 kiolvasása → (x:{region1.get('x',0)}, y:{region1.get('y',0)}, w:{region1.get('width',0)}, h:{region1.get('height',0)})")
            text1 = ImageManager.read_text_from_region(region1)
            log.info(f"Régió 1 OCR: '{text1}'")
        else:
            text1 = ""
            log.warning("Régió 1 nincs beállítva")

        # Régió 2 kiolvasás
        if region2:
            log.ocr(f"Régió 2 kiolvasása → (x:{region2.get('x',0)}, y:{region2.get('y',0)}, w:{region2.get('width',0)}, h:{region2.get('height',0)})")
            text2 = ImageManager.read_text_from_region(region2)
            log.info(f"Régió 2 OCR: '{text2}'")
        else:
            text2 = ""
            log.warning("Régió 2 nincs beállítva")

        # Régió 3 kiolvasás (ÚJ!)
        if region3:
            log.ocr(f"Régió 3 kiolvasása → (x:{region3.get('x',0)}, y:{region3.get('y',0)}, w:{region3.get('width',0)}, h:{region3.get('height',0)})")
            text3 = ImageManager.read_text_from_region(region3)
            log.info(f"Régió 3 OCR: '{text3}'")
        else:
            text3 = ""
            log.warning("Régió 3 nincs beállítva")

        # % jelenlétének ellenőrzése (MIND A 3 régióban kell!)
        # JAVÍTVA: OR → AND (mind a 3 régióban kell % jel)
        percent_count = sum([
            1 if '%' in text1 else 0,
            1 if '%' in text2 else 0,
            1 if '%' in text3 else 0
        ])

        has_all_percent = '%' in text1 and '%' in text2 and '%' in text3

        if has_all_percent:
            log.success(f"✅ Mind a 3 régióban van felfedezés folyamatban (3/3 % jel)")
            need_exploration = False
        else:
            log.warning(f"⚠️ Hiányzó felfedezés! ({percent_count}/3 % jel)")

            # INTELLIGENS POPUP DETEKTÁLÁS
            # Ha mind a 3 régió szemét szöveget tartalmaz → valószínű popup
            garbage_count = sum([
                1 if is_garbage_ocr_text(text1) else 0,
                1 if is_garbage_ocr_text(text2) else 0,
                1 if is_garbage_ocr_text(text3) else 0
            ])

            if garbage_count >= 2:
                log.warning(f"⚠️ Szemét OCR szövegek ({garbage_count}/3) → Popup valószínű!")
                log.info("🔍 X gomb keresés aktiválva (popup bezárás)...")

                # X gomb keresés és bezárás (régió alapú)
                search_region = self.popup_regions.get('popup_search_region')
                popup_closed = find_and_close_popups(search_region=search_region, max_attempts=3, threshold=0.7)

                if popup_closed:
                    log.success("✅ Popup bezárva! Scout panel újranyitása...")

                    # Scout panel újranyitása
                    delay = wait_random(self.human_wait_min, self.human_wait_max)
                    time.sleep(delay)

                    # Scout fül megnyitása újra
                    coords = self.coords.get('open_scout_tab', [0, 0])
                    log.click(f"Scout fül megnyitása (újra) → ({coords[0]}, {coords[1]})")
                    safe_click(coords)

                    # OCR újrapróbálás
                    delay = wait_random(self.human_wait_min, self.human_wait_max)
                    time.sleep(delay)

                    log.ocr("Felfedezés % újraolvasása (tiszta képernyő)...")

                    if region1:
                        text1 = ImageManager.read_text_from_region(region1)
                        log.info(f"Régió 1 OCR (újra): '{text1}'")
                    if region2:
                        text2 = ImageManager.read_text_from_region(region2)
                        log.info(f"Régió 2 OCR (újra): '{text2}'")
                    if region3:
                        text3 = ImageManager.read_text_from_region(region3)
                        log.info(f"Régió 3 OCR (újra): '{text3}'")

                    # Újra ellenőrzés
                    has_all_percent = '%' in text1 and '%' in text2 and '%' in text3

                    if has_all_percent:
                        log.success("✅ Popup bezárás után: Mind a 3 régióban van felfedezés!")
                        need_exploration = False
                    else:
                        log.warning("⚠️ Popup bezárás után is hiányzó felfedezés → Scout indítás")
                        need_exploration = True
                else:
                    log.warning("⚠️ X gomb nem található → Scout indítás szükséges")
                    need_exploration = True
            else:
                log.info("ℹ️ Normális OCR szövegek → Scout indítás szükséges")
                need_exploration = True

        # 5. Scout bezárása
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        coords = self.coords.get('close_scout', [0, 0])
        log.click(f"Scout bezárása → ({coords[0]}, {coords[1]})")
        safe_click(coords)

        # 6. Que fül megnyitása
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        coords = self.coords.get('open_queue_tab', [0, 0])
        log.click(f"Que fül megnyitása → ({coords[0]}, {coords[1]})")
        safe_click(coords)

        # 7. Que menü bezárása
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        coords = self.coords.get('close_queue_menu', [0, 0])
        log.click(f"Que menü bezárása → ({coords[0]}, {coords[1]})")
        safe_click(coords)

        log.separator('=', 60)

        return need_exploration

    def start_exploration(self):
        """
        Felfedezés indítása
        """
        log.separator('=', 60)
        log.info("🚀 EXPLORER - FELFEDEZÉS INDÍTÁSA")
        log.separator('=', 60)

        # 1. Scout épület
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp (emberi faktor)")
        time.sleep(delay)
        coords = self.coords.get('scout_building', [0, 0])
        log.click(f"Scout épület kattintás → ({coords[0]}, {coords[1]})")
        safe_click(coords)

        # 2. Pre-explore gomb (ÚJ!)
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        coords = self.coords.get('pre_explore_button', [0, 0])
        log.click(f"Pre-explore gomb → ({coords[0]}, {coords[1]})")
        safe_click(coords)

        # 3. Explore gomb (1. kattintás)
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        coords = self.coords.get('explore_button', [0, 0])
        log.click(f"Explore gomb (1. kattintás) → ({coords[0]}, {coords[1]})")
        safe_click(coords)

        # 4. Fix 1.5 mp várakozás
        log.wait("Fix várakozás 1.5 mp")
        time.sleep(1.5)

        # 5. Explore gomb (2. kattintás)
        log.click(f"Explore gomb (2. kattintás) → ({coords[0]}, {coords[1]})")
        safe_click(coords)

        # 6. Fix kattintás (képernyő közép)
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        coords = self.coords.get('screen_center', [0, 0])
        if coords != [0, 0]:
            log.click(f"Képernyő közép kattintás → ({coords[0]}, {coords[1]})")
            safe_click(coords)

        # 7. Space (1.)
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        log.action("SPACE billentyű lenyomása (1.)")
        press_key('space')

        # 8. Space (2.)
        delay = wait_random(self.human_wait_min, self.human_wait_max)
        log.wait(f"Várakozás {delay:.1f} mp")
        time.sleep(delay)
        log.action("SPACE billentyű lenyomása (2.)")
        press_key('space')

        log.success("✅ Felfedezés elindítva!")
        log.separator('=', 60)

    def run(self):
        """
        Teljes explorer ciklus

        Returns:
            str: "SUCCESS" ha sikeres volt
        """
        log.separator('#', 60)
        log.info("🔍 EXPLORER INDÍTÁSA")
        log.separator('#', 60)

        # Ellenőrzés
        need_exploration = self.check_exploration()

        # Ha kell, indítás
        if need_exploration:
            self.start_exploration()
        else:
            log.info("Nincs szükség új felfedezés indítására")

        log.separator('#', 60)
        log.success("🔍 EXPLORER BEFEJEZVE")
        log.separator('#', 60)

        return "SUCCESS"


def main():
    """Main entry point"""
    from library import initialize_game_window

    # Játék ablak inicializálása
    if not initialize_game_window("BlueStacks"):
        log.error("❌ Játék ablak nem található!")
        return

    # Explorer indítása
    try:
        explorer = Explorer()
        explorer.run()
    except KeyboardInterrupt:
        log.separator('#', 60)
        log.warning("⚠️ FELHASZNÁLÓ ÁLTAL MEGSZAKÍTVA (CTRL+C)")
        log.separator('#', 60)
    except Exception as e:
        log.separator('#', 60)
        log.error(f"KRITIKUS HIBA: {str(e)}")
        log.separator('#', 60)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
