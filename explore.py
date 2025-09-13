#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explore Script
Automatikusan megkeresi és használja az Explore funkciókat.
"""

import pyautogui
import time
import random
import os
import sys

# Library hozzáadása
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import library as lib


class ExploreBot:
    def __init__(self):
        """Explore bot inicializálása"""
        self.cycle_count = 0
        self.error_count = 0
        self.max_errors = 5

        # PyAutoGUI beállítások
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

        print("🗺️ EXPLORE BOT INICIALIZÁLÁSA")
        print("=" * 50)

        # Multi-monitor info
        lib.debug_multi_monitor_info()

    def find_text_explore(self, retries=5):
        """Megkeresi az 'Explore' szöveget OCR-rel"""
        print("🔍 Keresem 'Explore' szöveget...")

        for attempt in range(retries):
            coords = lib.find_text_multi_monitor("Explore", retries=1, delay=0.5)
            if coords:
                print(f"✅ 'Explore' szöveg találva: {coords}")
                return coords

            print(f"   Próbálkozás {attempt + 1}/{retries}...")
            time.sleep(1)

        print("❌ 'Explore' szöveg nem található")
        return None

    def find_explore_icon(self, retries=5):
        """Megkeresi az explore_icon.png-t"""
        print("🔍 Keresem explore_icon.png-t...")

        # Automatikus template keresés a library rendszerrel
        icon_path = "images/explore_icon.png"

        for attempt in range(retries):
            coords = lib.find_image(icon_path, retries=1, delay=0.5)
            if coords:
                print(f"✅ Explore ikon találva: {coords}")
                return coords

            print(f"   Próbálkozás {attempt + 1}/{retries}...")
            time.sleep(1)

        print("❌ Explore ikon nem található")
        return None

    def find_send_button(self, retries=5):
        """Megkeresi a Send gombot"""
        print("🔍 Keresem 'Send' gombot...")

        # Próbáljuk szöveggel
        for attempt in range(retries):
            coords = lib.find_text_multi_monitor("Send", retries=1, delay=0.5)
            if coords:
                print(f"✅ 'Send' gomb találva: {coords}")
                return coords

            print(f"   Próbálkozás {attempt + 1}/{retries}...")
            time.sleep(1)

        print("❌ 'Send' gomb nem található")
        return None

    def safe_click(self, coords, description=""):
        """Biztonságos kattintás koordinátákra"""
        if not coords:
            print(f"❌ Érvénytelen koordináták: {description}")
            return False

        try:
            # Koordináták javítása ha szükséges
            fixed_coords = lib.fix_coordinates(coords)
            if not fixed_coords:
                print(f"❌ Koordináta javítás sikertelen: {description}")
                return False

            pyautogui.click(fixed_coords)
            print(f"✅ Kattintás: {description} @ {fixed_coords}")
            return True

        except Exception as e:
            print(f"❌ Kattintási hiba {description}: {e}")
            return False

    def wait_random(self, min_time=1.0, max_time=3.0):
        """Véletlenszerű várakozás"""
        wait_time = random.uniform(min_time, max_time)
        print(f"⏳ Várakozás {wait_time:.1f} másodperc...")
        time.sleep(wait_time)

    def run_explore_cycle(self):
        """Egy teljes explore ciklus futtatása"""
        print(f"\n{'=' * 60}")
        print(f"🗺️ EXPLORE CIKLUS #{self.cycle_count + 1}")
        print(f"{'=' * 60}")

        steps_completed = 0

        try:
            # 1. LÉPÉS: Explore szöveg keresése és kattintás
            print("\n📍 1. LÉPÉS: Explore szöveg keresése...")
            explore_text_coords = self.find_text_explore()
            if not explore_text_coords:
                print("❌ 1. lépés sikertelen - újrakezdem a ciklust")
                return False

            if not self.safe_click(explore_text_coords, "Explore szöveg"):
                return False

            self.wait_random(2.0, 4.0)
            steps_completed += 1

            # 2. LÉPÉS: Explore ikon keresése és kattintás
            print("\n📍 2. LÉPÉS: Explore ikon keresése...")
            explore_icon_coords = self.find_explore_icon()
            if not explore_icon_coords:
                print("❌ 2. lépés sikertelen - újrakezdem a ciklust")
                return False

            if not self.safe_click(explore_icon_coords, "Explore ikon"):
                return False

            self.wait_random(2.0, 4.0)
            steps_completed += 1

            # 3. LÉPÉS: Explore szöveg újra keresése és kattintás
            print("\n📍 3. LÉPÉS: Explore szöveg újra keresése...")
            explore_text_coords2 = self.find_text_explore()
            if not explore_text_coords2:
                print("❌ 3. lépés sikertelen - újrakezdem a ciklust")
                return False

            if not self.safe_click(explore_text_coords2, "Explore szöveg (2.)"):
                return False

            self.wait_random(2.0, 4.0)
            steps_completed += 1

            # 4. LÉPÉS: explore.png újra keresése és kattintás
            print("\n📍 4. LÉPÉS: explore.png újra keresése...")
            explore_coords3 = self.find_explore_png()
            if not explore_coords3:
                print("❌ 4. lépés sikertelen - újrakezdem a ciklust")
                return False

            if not self.safe_click(explore_coords3, "explore.png (3.)"):
                return False

            self.wait_random(2.0, 4.0)
            steps_completed += 1

            # 5. LÉPÉS: Send gomb keresése és kattintás
            print("\n📍 5. LÉPÉS: Send gomb keresése...")
            send_coords = self.find_send_button()
            if not send_coords:
                print("❌ 5. lépés sikertelen - újrakezdem a ciklust")
                return False

            if not self.safe_click(send_coords, "Send gomb"):
                return False

            self.wait_random(1.0, 2.0)
            steps_completed += 1

            # 6. LÉPÉS: Space lenyomása
            print("\n📍 6. LÉPÉS: Space lenyomása...")
            pyautogui.press('space')
            print("✅ Space lenyomva")

            self.wait_random(3.0, 5.0)
            steps_completed += 1

            print(f"\n🎉 CIKLUS SIKERES! {steps_completed}/6 lépés teljesítve")
            self.cycle_count += 1
            self.error_count = 0  # Reset error counter on success
            return True

        except KeyboardInterrupt:
            print(f"\n🛑 Ciklus megszakítva felhasználó által")
            raise
        except Exception as e:
            print(f"\n❌ Váratlan hiba a ciklusban: {e}")
            print(f"📊 Teljesített lépések: {steps_completed}/6")
            return False

    def run(self):
        """Fő futási ciklus"""
        print("\n🚀 EXPLORE BOT INDÍTÁSA!")
        print("🛑 CTRL+C a megállításhoz")
        print("📍 Failsafe: Vidd az egeret a képernyő sarkába vészleállításhoz")

        # Rövid várakozás az induláskor
        print("\n⏳ Indítás 3 másodperc múlva...")
        time.sleep(3)

        try:
            while True:
                success = self.run_explore_cycle()

                if success:
                    print(f"✅ Összesen {self.cycle_count} sikeres ciklus")
                    self.wait_random(5.0, 8.0)  # Hosszabb szünet ciklusok között
                else:
                    self.error_count += 1
                    print(f"❌ Sikertelen ciklus ({self.error_count}/{self.max_errors})")

                    if self.error_count >= self.max_errors:
                        print(f"🛑 Túl sok hiba ({self.max_errors}), leállítás...")
                        break

                    # Hosszabb várakozás hiba után
                    print("🔄 Újrapróbálkozás 10 másodperc múlva...")
                    time.sleep(10)

        except KeyboardInterrupt:
            print(f"\n🛑 Program leállítva felhasználó által")
            print(f"📊 Összesen {self.cycle_count} sikeres ciklus futott")
        except Exception as e:
            print(f"\n❌ Kritikus hiba: {e}")
            import traceback
            traceback.print_exc()

        print("\n👋 Explore Bot leáll...")


def create_explore_template():
    """Segédprogram explore_icon.png template készítéséhez"""
    print("\n🎯 EXPLORE IKON TEMPLATE KÉSZÍTŐ")
    print("=" * 40)
    print("1. Keresd meg az explore ikont a játékban")
    print("2. Vidd az egeret az ikon közepére")
    print("3. Nyomj ENTER-t")

    input("\nNyomj ENTER-t amikor az egér az ikon fölött van...")

    try:
        pos = pyautogui.position()
        print(f"📍 Pozíció: {pos}")

        # Különböző méretű template-ek készítése
        sizes = [40, 60, 80, 100]
        images_folder = "images/"
        os.makedirs(images_folder, exist_ok=True)

        for size in sizes:
            half_size = size // 2
            region = (pos.x - half_size, pos.y - half_size, size, size)

            screenshot = pyautogui.screenshot(region=region)
            filename = f"explore_icon_{size}x{size}.png"
            filepath = os.path.join(images_folder, filename)

            screenshot.save(filepath)
            print(f"✅ {filename} mentve")

        # Fő template
        screenshot = pyautogui.screenshot(region=(pos.x - 40, pos.y - 40, 80, 80))
        filepath = os.path.join(images_folder, "explore_icon.png")
        screenshot.save(filepath)
        print(f"✅ explore_icon.png mentve")

        print(f"\n📁 Template-ek helye: {os.path.abspath(images_folder)}")

    except Exception as e:
        print(f"❌ Hiba: {e}")


def main():
    """Fő program"""
    print("🗺️ EXPLORE SCRIPT")
    print("=" * 30)
    print("1. Explore bot futtatása")
    print("2. Explore ikon template készítése")
    print("3. Scout tent template készítése")
    print("4. Kilépés")

    while True:
        choice = input("\nVálasztás (1-4): ").strip()

        if choice == "1":
            # Ellenőrizzük a szükséges template-eket
            missing_templates = []

            explore_icon_path = "images/explore_icon.png"
            scout_tent_path = "images/scout-tent.png"

            if not os.path.exists(explore_icon_path):
                missing_templates.append("explore_icon.png")

            if not os.path.exists(scout_tent_path):
                missing_templates.append("scout-tent.png")

            if missing_templates:
                print(f"⚠️ Hiányzó template-ek: {', '.join(missing_templates)}")
                print("💡 Először készítsd el a szükséges template-eket")

                for template in missing_templates:
                    if "scout" in template:
                        create_now = input(f"Készítsem el a {template}-et most? (y/N): ").strip().lower()
                        if create_now in ['y', 'yes', 'igen']:
                            create_scout_tent_template()
                    else:
                        create_now = input(f"Készítsem el a {template}-et most? (y/N): ").strip().lower()
                        if create_now in ['y', 'yes', 'igen']:
                            create_explore_template()

                print("\n🔄 Most már futtathatod a botot!")
                continue

            # Bot futtatása
            bot = ExploreBot()
            bot.run()
            break

        elif choice == "2":
            create_explore_template()

        elif choice == "3":
            create_scout_tent_template()

        elif choice == "4":
            print("👋 Kilépés...")
            break

        else:
            print("❌ Érvénytelen választás!")


if __name__ == "__main__":
    main()