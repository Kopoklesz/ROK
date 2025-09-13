import pyautogui
import time
import random
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import library as lib


def analyze_farm(farm_type, image_path):
    """Megkeresi a farmot és kiszámolja a megtelési időt."""
    # Változóként használjuk az image_path-ot
    coords = lib.wait_for_image_forever(image_path, delay=2)
    if not coords:
        print(f"❌ Nem találtam farmot: {farm_type}")
        return None

    # katt a farmra
    pyautogui.click(coords)
    time.sleep(2)
    pyautogui.click(coords)
    print(f"✅ Kattintottam {farm_type} farmra")
    time.sleep(random.uniform(1.0, 2.5))

    # information ikon
    coords_info = lib.find_with_backups("../images/information_icon.png", retries=10, delay=2)
    if not coords_info:
        print("❌ Nem találtam information_icon-t")
        return None
    pyautogui.click(coords_info)
    time.sleep(random.uniform(1.0, 2.5))

    # Production/Hour
    prod = lib.find_label_and_two_numbers("Production/Hour")
    if not prod:
        print("❌ Nem találtam Production/Hour feliratot")
        return None

    # Capacity
    cap = lib.find_label_and_two_numbers("Capacity")
    if not cap:
        print("❌ Nem találtam Capacity feliratot")
        return None

    # számítás
    seconds, prod_total, cap_total = lib.calculate_fill_time(prod, cap)
    print(f"📊 {farm_type} farm → Prod: {prod_total}, Cap: {cap_total}, Time: {seconds}s")

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
    print(f"⏳ Várakozás {wait_time} mp-ig ({wait_time/60:.1f} perc)...")
    time.sleep(wait_time)

    # Visszatérés a farmra
    coords = best_farm["coords"]
    pyautogui.click(coords)
    time.sleep(2)
    pyautogui.click(coords)
    print(f"🌾 Leharatva a {farm_type} farm!")

    return True


def main():
    farm_types = {
        "stone": "../images/stone_farm.png",
        "wheat": "../images/wheat_farm.png",
        "gold": "../images/gold_farm.png",
        "wood": "../images/wood_farm.png",
    }

    while True:
        for farm_type, img in farm_types.items():
            print(f"\n=== {farm_type.upper()} farm ciklus ===")
            success = run_cycle(farm_type, img)
            if not success:
                print(f"❌ {farm_type} farm ciklus sikertelen, újrapróbálkozás...")
            time.sleep(3)  # kis pihenő minden kör között


if __name__ == "__main__":
    main()
