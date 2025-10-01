from library import ImageManager, WindowManager, MultiMonitorManager, initialize_game_window, safe_click
import time
import random
import subprocess
from pynput.keyboard import Controller, Key
from pynput import mouse
from datetime import datetime

class ExploreScript:
    def __init__(self, first_coord, second_coord, explore_templates, send_template, backup_template=None):
        self.first_coord = first_coord
        self.second_coord = second_coord
        self.explore_templates = explore_templates
        self.send_template = send_template
        self.backup_template = backup_template

        # Ablak inicializálása
        if not initialize_game_window():
            raise RuntimeError("❌ Nem található a játék ablak!")

        self.win_mgr = WindowManager()
        self.mon_mgr = MultiMonitorManager()
        self.image_mgr = ImageManager(self.win_mgr, self.mon_mgr)
        self.keyboard = Controller()

        # Manuális kattintások logolása
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()

    def log(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {msg}")

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.log(f"🖱 Manuális kattintás: ({x}, {y}) gomb: {button}")

    def click_safe(self, coords, desc=""):
        if coords:
            safe_click(coords)
            self.log(f"✅ Kattintás {desc} -> Koordináták: {coords}")
            delay = random.randint(2, 5)
            self.log(f"⏳ Várakozás {delay} mp a következő lépés előtt...")
            time.sleep(delay)

    def find_image_with_timeout(self, template_list, timeout=15):
        """Keresés adott template listára max timeout-ig, visszatér koordinátával vagy None."""
        start_time = time.time()
        while True:
            for tpl in template_list:
                coords = self.image_mgr.find_image(tpl)
                if coords:
                    return coords, tpl
            if time.time() - start_time > timeout:
                return None, None
            time.sleep(0.5)

    def run(self):
        # 1. Első fix koordináta
        self.log(f"🔹 Kattintás első fix koordinátára: {self.first_coord}")
        self.click_safe(self.first_coord, "Első fix koordináta")

        # 2. Második fix koordináta
        self.log(f"🔹 Kattintás második fix koordinátára: {self.second_coord}")
        self.click_safe(self.second_coord, "Második fix koordináta")

        # 3. Első explore kép
        coords, tpl = self.find_image_with_timeout(self.explore_templates, timeout=15)
        if coords:
            self.click_safe(coords, f"Explore ikon ({tpl})")
        else:
            self.log("⚠️ Explore ikon nem található 15 mp alatt, script leáll")
            return

        # 4. Második explore kép (fix koordináta)
        second_explore_coord = (1208, 717)
        self.log(f"🔹 Kattintás második explore fix koordinátára: {second_explore_coord}")
        self.click_safe(second_explore_coord, "Második explore fix koordináta")

        # 5. Send ikon
        coords, tpl = self.find_image_with_timeout([self.send_template], timeout=15)
        if coords:
            self.click_safe(coords, f"Send ikon ({tpl})")
            self.keyboard.press(Key.space)
            self.keyboard.release(Key.space)
            self.log(f"⏩ Space lenyomva a send után -> Koordináták: {coords}")
        elif self.backup_template:
            coords, tpl = self.find_image_with_timeout([self.backup_template], timeout=10)
            if coords:
                self.click_safe(coords, f"Backup ikon ({tpl})")
                self.keyboard.press(Key.space)
                self.keyboard.release(Key.space)
                self.log(f"⏩ Space lenyomva backup után -> Koordináták: {coords}")
            else:
                self.log("⚠️ Send és backup ikon sem található, space lenyomva")
                self.keyboard.press(Key.space)
                self.keyboard.release(Key.space)
        else:
            self.log("⚠️ Send ikon nem található, space lenyomva")
            self.keyboard.press(Key.space)
            self.keyboard.release(Key.space)

        self.log("✅ Teljes kör végrehajtva, script kész.")

if __name__ == "__main__":
    first_coord = (997, 171)
    second_coord = (1202, 584)
    explore_templates = [
        "images/explore_d.png",
        "images/explore_e.png"
    ]
    send_template = "images/send.png"
    backup_template = "images/backup.png"  # opcionális

    script = ExploreScript(first_coord, second_coord, explore_templates, send_template, backup_template)
    script.run()
