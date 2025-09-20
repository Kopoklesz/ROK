from library import ImageManager, WindowManager, MultiMonitorManager, initialize_game_window, safe_click
import time
import random
import subprocess
import os
import sys
from pynput.keyboard import Controller, Key
from datetime import datetime

class IconCollector:
    def __init__(self, icons, scout_icon, backup_icon=None, explore_script_path=None):
        self.icons = icons
        self.scout_icon = scout_icon
        self.backup_icon = backup_icon
        self.explore_script_path = explore_script_path

        # Ablak inicializálása
        if not initialize_game_window():
            raise RuntimeError("❌ Nem található a játék ablak!")

        self.win_mgr = WindowManager()
        self.mon_mgr = MultiMonitorManager()
        self.image_mgr = ImageManager(self.win_mgr, self.mon_mgr)
        self.keyboard = Controller()

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def is_explore_running(self):
        for p in os.popen('tasklist').read().splitlines():
            if "explore_script.py" in p:
                return True
        return False

    def gather_next_icon(self, max_search_time=15):
        start_time = time.time()
        while True:
            if self.is_explore_running():
                self.log("⚠️ explore_script.py fut, várakozás...")
                time.sleep(1)
                continue

            # csak az aktuális script ikonja
            for icon_path in self.icons:
                coords = self.image_mgr.find_image(icon_path)
                if coords:
                    # help icon +60 px
                    if "help_icon" in icon_path:
                        x, y = coords
                        y += 60
                        coords = (x, y)
                        self.log(f"ℹ️ Help ikon esetén módosított koordináták: {coords}")

                    self.log(f"✅ Ikon megtalálva: {icon_path} -> {coords}")
                    safe_click(coords)
                    self.log(f"🖱 Kattintás az ikonra: {icon_path} -> Koordináták: {coords}")
                    delay = random.randint(5, 10)
                    self.log(f"⏳ Várakozás {delay} mp a következő ikon előtt...")
                    time.sleep(delay)
                    return  # csak az első megtalált ikon

            # Scout ikon külön
            if self.scout_icon:
                coords = self.image_mgr.find_image(self.scout_icon)
                if coords:
                    self.log(f"✅ Scout ikon megtalálva: {coords}")
                    safe_click(coords)
                    return
                elif time.time() - start_time > max_search_time and self.explore_script_path:
                    self.log("⚠️ Scout ikon nem található, explore_script futtatása...")
                    subprocess.Popen([sys.executable, self.explore_script_path])
                    return

            # Backup / space ha elakadt
            if time.time() - start_time > max_search_time:
                if self.backup_icon:
                    coords = self.image_mgr.find_image(self.backup_icon)
                    if coords:
                        self.log(f"⚠️ Backup ikon megtalálva: {self.backup_icon} -> {coords}")
                        safe_click(coords)
                        return
                self.log("⚠️ Nincs ikon 15 mp alatt, space lenyomva")
                self.keyboard.press(Key.space)
                self.keyboard.release(Key.space)
                return

            time.sleep(0.5)

    def run_forever(self):
        while True:
            self.gather_next_icon()


if __name__ == "__main__":
    # Példa ikonok
    icons = [
        "images/gold_icon.png",
        "images/wheat_icon.png",
        "images/stone_icon.png",
        "images/wood_icon.png",
        "images/help_icon.png",
    ]
    scout_icon = "images/scout_icon.png"
    backup_icon = "images/backup_icon.png"
    explore_script_path = "explore_script.py"

    collector = IconCollector(icons, scout_icon, backup_icon, explore_script_path)
    collector.run_forever()
