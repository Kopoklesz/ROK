#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Template Készítő Script
Segít új template-ek létrehozásában a játékból.
Futtatás: python template_creator.py
"""

import os
import sys
import time
import pyautogui

# Library hozzáadása
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import library as lib


def create_all_templates():
    """Minden farm típushoz készít template-eket"""
    print("🎯 TEMPLATE KÉSZÍTŐ MASTER SCRIPT")
    print("=" * 50)
    print("Ez a script segít template-eket készíteni minden farm típushoz.")
    print("Minden farm típusnál különböző méretű template-eket hoz létre.")
    print("\nLÉPÉSEK:")
    print("1. Nyisd meg a játékot")
    print("2. Menj a farm nézetre ahol láthatók a farmok")
    print("3. A script kéri hogy vidd az egeret a farmra")
    print("4. ENTER-rel megerősítve screenshot készül")
    print("5. Ismételd meg minden farm típussal")

    input("\nNyomj ENTER-t ha készen állsz...")

    farm_types = {
        "1": "stone_farm",
        "2": "wheat_farm",
        "3": "gold_farm",
        "4": "wood_farm",
        "5": "information_icon"  # Information ikon is kell
    }

    images_folder = "../images/"
    os.makedirs(images_folder, exist_ok=True)

    completed = []

    while len(completed) < len(farm_types):
        print(f"\n{'=' * 50}")
        print("FARM TÍPUSOK:")
        for key, farm in farm_types.items():
            status = "✅ KÉSZ" if farm in completed else "❌ NINCS"
            print(f"  {key}. {farm:<20} {status}")
        print("  s. Állapot ellenőrzés")
        print("  q. Kilépés")

        choice = input(f"\nVálassz farm típust ({len(completed)}/{len(farm_types)} kész): ").strip()

        if choice.lower() == 'q':
            break
        elif choice.lower() == 's':
            check_existing_templates()
            continue
        elif choice in farm_types:
            farm_name = farm_types[choice]

            if farm_name in completed:
                print(f"✅ {farm_name} már elkészült!")
                continue

            print(f"\n🎯 {farm_name.upper()} TEMPLATE KÉSZÍTÉSE")
            print("-" * 30)
            print("1. Vidd az egeret a farm/ikon közepére")
            print("2. Várd meg az 5 másodperces visszaszámlálást")
            print("3. Tartsd mozdulatlanul az egeret!")

            try:
                # Visszaszámlálás
                for i in range(5, 0, -1):
                    print(f"⏱️  {i} másodperc...")
                    time.sleep(1)

                pos = pyautogui.position()
                print(f"📍 Screenshot pozíció: {pos}")

                # Több méretű template készítése
                sizes = [40, 60, 80, 100, 120]
                success_count = 0

                for size in sizes:
                    try:
                        half_size = size // 2
                        region = (pos.x - half_size, pos.y - half_size, size, size)

                        # Ellenőrizzük hogy a régió nem megy ki a képernyőről
                        screen_size = pyautogui.size()
                        if (region[0] < 0 or region[1] < 0 or
                                region[0] + region[2] > screen_size.width or
                                region[1] + region[3] > screen_size.height):
                            print(f"   ⚠️  {size}x{size}: Képernyőn kívül esne")
                            continue

                        screenshot = pyautogui.screenshot(region=region)
                        filename = f"{farm_name}_{size}x{size}.png"
                        filepath = os.path.join(images_folder, filename)

                        screenshot.save(filepath)
                        print(f"   ✅ {filename}")
                        success_count += 1

                    except Exception as e:
                        print(f"   ❌ {size}x{size}: {e}")

                if success_count > 0:
                    print(f"🎉 {farm_name}: {success_count} template sikeresen létrehozva!")
                    completed.append(farm_name)

                    # Opcionálisan készítünk egy "a", "b", "c" verziót is
                    create_variants = input("Készítsek variáns template-eket is? (y/N): ").strip().lower()
                    if create_variants in ['y', 'yes']:
                        create_variant_templates(farm_name, pos, images_folder)
                else:
                    print(f"❌ {farm_name}: Nem sikerült template-et készíteni!")

            except Exception as e:
                print(f"❌ Hiba történt {farm_name} készítése közben: {e}")

        else:
            print("❌ Érvénytelen választás!")

    # Összefoglaló
    print(f"\n{'=' * 50}")
    print("🏁 TEMPLATE KÉSZÍTÉS BEFEJEZVE")
    print(f"✅ Elkészült: {len(completed)} / {len(farm_types)}")
    for farm in completed:
        print(f"   ✅ {farm}")

    missing = [farm for farm in farm_types.values() if farm not in completed]
    if missing:
        print(f"❌ Hiányzik: {len(missing)}")
        for farm in missing:
            print(f"   ❌ {farm}")

    print(f"\n📁 Template-ek helye: {os.path.abspath(images_folder)}")
    print("🚀 Most már futtathatod a gathering_script.py-t!")


def create_variant_templates(farm_name, center_pos, images_folder):
    """Variáns template-ek készítése (a, b, c verziók)"""
    print(f"\n🔄 Variáns template-ek készítése {farm_name}-hez...")

    # Kis eltérésekkel készítünk template-eket
    variants = [
        ("a", -10, -5),  # Balra-fel
        ("b", 10, -5),  # Jobbra-fel
        ("c", 0, 10),  # Középen-le
    ]

    for variant_name, dx, dy in variants:
        try:
            new_pos = pyautogui.Point(center_pos.x + dx, center_pos.y + dy)

            # 80x80-as template készítése
            region = (new_pos.x - 40, new_pos.y - 40, 80, 80)

            # Képernyő boundary ellenőrzés
            screen_size = pyautogui.size()
            if (region[0] >= 0 and region[1] >= 0 and
                    region[0] + region[2] <= screen_size.width and
                    region[1] + region[3] <= screen_size.height):

                screenshot = pyautogui.screenshot(region=region)
                filename = f"{farm_name}_{variant_name}.png"
                filepath = os.path.join(images_folder, filename)
                screenshot.save(filepath)
                print(f"   ✅ {filename}")
            else:
                print(f"   ⚠️  {variant_name}: Képernyőn kívül")

        except Exception as e:
            print(f"   ❌ {variant_name}: {e}")


def check_existing_templates():
    """Meglévő template-ek ellenőrzése"""
    print("\n📋 MEGLÉVŐ TEMPLATE-EK ELLENŐRZÉSE")
    print("-" * 40)

    images_folder = "../images/"
    farm_types = ["stone_farm", "wheat_farm", "gold_farm", "wood_farm", "information_icon"]

    for farm_name in farm_types:
        templates = lib.find_template_files(farm_name, images_folder)
        if templates:
            print(f"✅ {farm_name}: {len(templates)} template")
            for template in templates:
                size = os.path.getsize(template)
                print(f"   📄 {os.path.basename(template)} ({size} bytes)")
        else:
            print(f"❌ {farm_name}: Nincs template")


def quick_single_template():
    """Gyors egyszeri template készítés"""
    print("\n⚡ GYORS TEMPLATE KÉSZÍTÉS")
    print("Vidd az egeret a kívánt helyre és nyomj ENTER-t!")

    farm_name = input("Farm név (pl. stone_farm_extra): ").strip()
    if not farm_name:
        print("❌ Érvénytelen név!")
        return

    input("Nyomj ENTER-t amikor az egér a megfelelő helyen van...")

    pos = pyautogui.position()
    region = (pos.x - 40, pos.y - 40, 80, 80)

    try:
        screenshot = pyautogui.screenshot(region=region)
        filename = f"{farm_name}.png"
        filepath = os.path.join("../images/", filename)

        os.makedirs("../images/", exist_ok=True)
        screenshot.save(filepath)
        print(f"✅ Mentve: {filename}")

    except Exception as e:
        print(f"❌ Hiba: {e}")


def batch_template_creator():
    """Batch módú template készítés - egyszerűbb verzió"""
    print("\n🔥 BATCH TEMPLATE KÉSZÍTŐ")
    print("=" * 40)
    print("Egyszerűsített verzió minden farm típushoz!")
    print("\nMinden farmnál:")
    print("1. Vidd az egeret a farm fölé")
    print("2. Nyomj SPACE-t")
    print("3. Folytasd a következő farmmal")
    print("4. ESC a kilépéshez")

    farm_types = ["stone_farm", "wheat_farm", "gold_farm", "wood_farm", "information_icon"]
    images_folder = "../images/"
    os.makedirs(images_folder, exist_ok=True)

    current_farm = 0

    print(f"\n🎯 Kezdés: {farm_types[current_farm].upper()}")
    print("Vidd az egeret a farm fölé és nyomj SPACE-t!")

    while current_farm < len(farm_types):
        try:
            # Várunk egy billentyűre
            key = input("SPACE = screenshot, ESC = kilépés, ENTER = következő: ").strip().lower()

            if key == '' or key == 'space' or key == ' ':
                # Screenshot készítés
                farm_name = farm_types[current_farm]
                pos = pyautogui.position()

                # 80x80-as template
                region = (pos.x - 40, pos.y - 40, 80, 80)
                screenshot = pyautogui.screenshot(region=region)
                filename = f"{farm_name}.png"
                filepath = os.path.join(images_folder, filename)
                screenshot.save(filepath)

                print(f"✅ {filename} mentve @ {pos}")

                # Következő farm
                current_farm += 1
                if current_farm < len(farm_types):
                    print(f"\n🎯 Következő: {farm_types[current_farm].upper()}")
                    print("Vidd az egeret a farm fölé és nyomj SPACE-t!")
                else:
                    print("\n🎉 Minden template elkészült!")
                    break

            elif key == 'esc' or key == 'escape' or key == 'q':
                print("👋 Kilépés...")
                break

        except KeyboardInterrupt:
            print("\n👋 Megszakítva...")
            break
        except Exception as e:
            print(f"❌ Hiba: {e}")

    print(f"\n📁 Template-ek helye: {os.path.abspath(images_folder)}")


if __name__ == "__main__":
    # PyAutoGUI beállítások
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1

    print("🎯 TEMPLATE KÉSZÍTŐ SEGÉDPROGRAM")
    print("=" * 40)
    print("1. Teljes template készítés (részletes)")
    print("2. Batch template készítés (gyors)")
    print("3. Meglévő template-ek ellenőrzése")
    print("4. Gyors egyedi template")
    print("5. Kilépés")

    while True:
        choice = input("\nVálasztás (1-5): ").strip()

        if choice == "1":
            create_all_templates()
            break
        elif choice == "2":
            batch_template_creator()
            break
        elif choice == "3":
            check_existing_templates()
        elif choice == "4":
            quick_single_template()
        elif choice == "5":
            print("👋 Kilépés...")
            break
        else:
            print("❌ Érvénytelen választás!")