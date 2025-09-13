import pyautogui
import time
import random
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import library as lib


def analyze_farm(farm_type, image_path):
    """Megkeresi a farmot és kiszámolja a megtelési időt - most multi-monitor + multi-template támogatással."""
    print(f"\n🔍 Keresem {farm_type} farmot...")

    # Az új multi-monitor + multi-template támogatással automatikusan keres minden monitoron és template-tel
    coords = lib.wait_for_image_forever(image_path, delay=2)
    if not coords:
        print(f"❌ Nem találtam farmot: {farm_type}")
        return None

    # katt a farmra
    pyautogui.click(coords)
    time.sleep(2)
    pyautogui.click(coords)
    print(f"✅ Kattintottam {farm_type} farmra a koordinátán: {coords}")
    time.sleep(random.uniform(1.0, 2.5))

    # information ikon keresése - multi-monitor + multi-template támogatással
    print("🔍 Keresem information ikont...")
    coords_info = lib.find_with_backups("../images/information_icon.png", retries=10, delay=2)
    if not coords_info:
        print("❌ Nem találtam information_icon-t")
        return None

    pyautogui.click(coords_info)
    print(f"✅ Kattintottam information ikonra: {coords_info}")
    time.sleep(random.uniform(1.0, 2.5))

    # Production/Hour keresése - multi-monitor támogatással
    print("📊 Keresem Production/Hour adatokat...")
    prod = lib.find_label_and_two_numbers("Production/Hour")
    if not prod:
        print("❌ Nem találtam Production/Hour feliratot")
        return None

    # Capacity keresése - multi-monitor támogatással
    print("📊 Keresem Capacity adatokat...")
    cap = lib.find_label_and_two_numbers("Capacity")
    if not cap:
        print("❌ Nem találtam Capacity feliratot")
        return None

    # számítás
    seconds, prod_total, cap_total = lib.calculate_fill_time(prod, cap)
    print(f"📊 {farm_type} farm → Prod: {prod_total}, Cap: {cap_total}, Time: {seconds}s ({seconds / 60:.1f} perc)")

    return {
        "type": farm_type,
        "coords": coords,
        "production": prod_total,
        "capacity": cap_total,
        "time_to_fill": seconds,
    }


def run_cycle(farm_type, image_path):
    """Kiválasztja a leggyorsabban megtelő farmot és visszatér oda a szükséges idő múlva."""
    best_farm = analyze_farm(farm_type, image_path)
    if not best_farm:
        return False

    # Várakozás a megtelésig
    wait_time = best_farm["time_to_fill"]
    wait_minutes = wait_time / 60
    print(f"⏳ Várakozás {wait_time} mp-ig ({wait_minutes:.1f} perc)...")

    # Ha túl hosszú a várakozási idő, részletesebb tájékoztatás
    if wait_minutes > 30:
        print(f"📅 Ez hosszabb várakozás lesz: {wait_minutes / 60:.1f} óra")
        # Opcionálisan itt lehetne rövidebb ciklusokban ellenőrizni

    time.sleep(wait_time)

    # Visszatérés a farmra - multi-monitor támogatással automatikusan megtalálja
    coords = best_farm["coords"]
    pyautogui.click(coords)
    time.sleep(2)
    pyautogui.click(coords)
    print(f"🌾 Leharatva a {farm_type} farm! Koordináta: {coords}")

    return True


def main():
    """Fő program - automatikus template rendszerrel és multi-monitor támogatással"""
    print("🚀 Farming Script indítása multi-monitor + auto-template támogatással!")

    # Multi-monitor és template debug info
    lib.debug_multi_monitor_info()
    lib.debug_template_system()

    # Automatikus template fájl detektálás
    farm_types = {}
    base_farm_names = ["stone_farm", "wheat_farm", "gold_farm", "wood_farm"]
    images_folder = "../images/"

    for farm_name in base_farm_names:
        templates = lib.find_template_files(farm_name, images_folder)
        if templates:
            farm_types[farm_name.replace("_farm", "")] = templates[0]  # Első template használata
            print(f"✅ {farm_name}: {len(templates)} template található")
        else:
            print(f"❌ {farm_name}: Nincs template! Template készítés szükséges.")

    if not farm_types:
        print("❌ Egyetlen farm template sem található!")
        print("💡 Futtasd a template készítőt: python template_creator.py")

        # Interaktív template készítés felajánlása
        create_now = input("\nKészítsek most template-eket? (y/N): ").strip().lower()
        if create_now in ['y', 'yes', 'igen']:
            lib.interactive_template_creator()
            print("\n🔄 Indítsd újra a scriptet a template-ek használatához!")
        return

    print(f"\n🎯 Aktív farmok: {list(farm_types.keys())}")

    cycle_count = 0

    try:
        while True:
            cycle_count += 1
            print(f"\n{'=' * 60}")
            print(f"🔄 CIKLUS #{cycle_count}")
            print(f"{'=' * 60}")

            for farm_type, template_path in farm_types.items():
                print(f"\n=== {farm_type.upper()} farm ciklus ===")
                success = run_cycle(farm_type, template_path)
                if not success:
                    print(f"❌ {farm_type} farm ciklus sikertelen, újrapróbálkozás...")
                else:
                    print(f"✅ {farm_type} farm ciklus sikeres!")

                time.sleep(3)  # kis pihenő minden kör között

    except KeyboardInterrupt:
        print(f"\n🛑 Program leállítva felhasználó által. Összesen {cycle_count} ciklus futott.")
    except Exception as e:
        print(f"\n❌ Váratlan hiba történt: {e}")
        print("🔄 Újraindítás ajánlott.")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()