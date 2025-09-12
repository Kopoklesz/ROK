import pyautogui
import time
import random
import library as lib   # a helper függvények

def run_cycle():
    """Egy teljes kör lefuttatása. Siker esetén True-t ad vissza."""
    
    # 1. Várjuk a png1-et
    coords = lib.wait_for_image("images/png1.png", delay=2)
    if not coords:
        return False
    pyautogui.click(coords)
    print("Kattintottam: png1")
    time.sleep(random.uniform(1.0, 2.5))

    # 2. png2 + backup képek
    coords = lib.find_with_backups(
        "images/png2.png",
        "images/png2b.png",
        "images/png2c.png",
        retries=10,
        delay=2
    )
    if not coords:
        # ha semmit nem talált, akkor vissza a png5-höz
        coords = lib.wait_for_image("images/png5.png", delay=2)
        if coords:
            pyautogui.click(coords)
            print("Nem találtam png2-t vagy backupjait → vissza png5")
        return False
    pyautogui.click(coords)
    print("Kattintottam: png2 (vagy backup)")
    time.sleep(random.uniform(1.0, 2.5))

    # 3. png3
    coords = lib.wait_for_image("images/png3.png", delay=2)
    if not coords:
        return False
    pyautogui.click(coords)
    print("Kattintottam: png3")
    time.sleep(random.uniform(1.0, 2.5))

    # 4. png4
    coords = lib.wait_for_image("images/png4.png", delay=2)
    if not coords:
        return False
    pyautogui.click(coords)
    print("Kattintottam: png4")
    time.sleep(random.uniform(1.0, 2.5))

    # 5. "gathering" szöveg
    coords = lib.wait_for_text("gathering", delay=2)
    if not coords:
        return False
    pyautogui.click(coords)
    print("Kattintottam: gathering")
    time.sleep(random.uniform(1.0, 2.5))

    # 6. png5
    coords = lib.wait_for_image("images/png5.png", delay=2)
    if not coords:
        return False
    pyautogui.click(coords)
    print("Kattintottam: png5")
    time.sleep(random.uniform(1.0, 2.5))

    return True


def main():
    success_count = 0
    while success_count < 80:
        print(f"\n--- {success_count+1}. kör ---")
        success = run_cycle()
        if success:
            success_count += 1
            print(f"Sikeres kör! ({success_count}/80)")
        else:
            print("Sikertelen kör, újrapróbálkozom...")

    print("✅ Script befejezte a 80 sikeres ciklust.")


if __name__ == "__main__":
    main()
