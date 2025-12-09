"""
ROK Auto Farm Manager
Fő ciklus - erőforrás ellenőrzés és farm kiválasztás
"""
import json
import time
import random
from pathlib import Path

from library import ImageManager, initialize_game_window
from utils.logger import FarmLogger as log
from utils.ocr_parser import parse_resource_value

from farms.wheat_farm import WheatFarm
from farms.wood_farm import WoodFarm
from farms.stone_farm import StoneFarm
from farms.gold_farm import GoldFarm
from explorer import Explorer


class FarmManager:
    """Auto Farm Manager - fő koordinátor"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent / 'config'
        
        # Konfigurációk betöltése
        self.settings = self._load_settings()
        self.farm_regions = self._load_farm_regions()
        
        # Paraméterek
        self.max_cycles = self.settings.get('max_cycles', 100)
        self.repeat_count = self.settings.get('repeat_count', 4)
        
        # Farm instance-ok
        self.farms = {
            'wheat': WheatFarm(),
            'wood': WoodFarm(),
            'stone': StoneFarm(),
            'gold': GoldFarm()
        }

        # Explorer instance
        self.explorer = Explorer()
    
    def _load_settings(self):
        """Settings.json betöltése"""
        settings_file = self.config_dir / 'settings.json'
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_farm_regions(self):
        """Erőforrás OCR régiók betöltése"""
        regions_file = self.config_dir / 'farm_regions.json'
        if regions_file.exists():
            with open(regions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def read_all_resources(self):
        """Összes erőforrás kiolvasása OCR-rel"""
        log.separator('=', 60)
        log.info("📊 ERŐFORRÁSOK KIOLVASÁSA")
        log.separator('=', 60)
        
        resources = {}
        
        for resource_name, region in self.farm_regions.items():
            if region is None:
                log.info(f"{resource_name.upper()}: Nincs beállítva, kihagyva")
                continue
            
            log.ocr(f"{resource_name.upper()} kiolvasása → Region: (x:{region['x']}, y:{region['y']}, w:{region['width']}, h:{region['height']})")
            
            ocr_text = ImageManager.read_text_from_region(region)
            log.info(f"OCR nyers szöveg: '{ocr_text}'")
            
            value = parse_resource_value(ocr_text)
            resources[resource_name] = value
            
            log.success(f"{resource_name.upper()}: {ocr_text} → {value:,} (parsed)")
        
        log.separator('=', 60)
        return resources
    
    def run(self):
        """Fő ciklus"""
        log.separator('#', 60)
        log.success("🚀 ROK AUTO FARM MANAGER ELINDULT")
        log.separator('#', 60)
        
        log.info(f"Max ciklusok: {self.max_cycles}")
        log.info(f"Ismétlések/farm: {self.repeat_count}")
        log.info(f"Emberi várakozás: {self.settings.get('human_wait_min', 3)}-{self.settings.get('human_wait_max', 8)} sec")
        log.info(f"Gather retry kísérletek: {self.settings.get('gather_retry_attempts', 25)}")
        
        # ===== INDÍTÁSI VÁRAKOZÁS 20-25 MP =====
        log.separator('=', 60)
        startup_wait = random.uniform(
            self.settings.get('startup_wait_min', 20),
            self.settings.get('startup_wait_max', 25)
        )
        log.warning(f"⏰ INDÍTÁSI VÁRAKOZÁS: {startup_wait:.1f} másodperc")
        log.info("Váltás a játékra és felkészülés...")
        log.separator('=', 60)
        
        # Countdown 5 másodpercenként
        remaining = startup_wait
        while remaining > 0:
            if remaining > 5:
                log.wait(f"Indulás {remaining:.0f} másodperc múlva...")
                time.sleep(5)
                remaining -= 5
            else:
                log.wait(f"Indulás {remaining:.0f} másodperc múlva...")
                time.sleep(remaining)
                remaining = 0
        
        log.success("✅ Várakozás vége, farmolás indítása!")
        log.separator('=', 60)
        
        # ===== FŐ CIKLUS =====
        current_cycle = 0
        
        while current_cycle < self.max_cycles:
            current_cycle += 1

            log.separator('#', 60)
            log.info(f"🔁 CIKLUS {current_cycle}/{self.max_cycles}")
            log.separator('#', 60)

            # 0. Explorer ellenőrzés (minden ciklus elején)
            try:
                log.info("🔍 Explorer ellenőrzés...")
                self.explorer.run()
            except Exception as e:
                log.warning(f"⚠️ Explorer hiba: {str(e)}")
                log.info("Folytatás farmolással...")

            # 1. Erőforrás kiolvasás
            resources = self.read_all_resources()
            
            if not resources:
                log.error("Nincs beállított erőforrás régió!")
                break
            
            # 2. Osztás és minimum keresés
            log.separator('-', 60)
            log.info("🧮 ERŐFORRÁS ÉRTÉKELÉS")
            log.separator('-', 60)
            
            values = {}
            for res, amount in resources.items():
                if res == 'wheat' or res == 'wood':
                    divisor = 4
                elif res == 'stone':
                    divisor = 3
                elif res == 'gold':
                    divisor = 2
                else:
                    divisor = 1
                
                values[res] = amount / divisor
                log.info(f"{res.upper()}: {amount:,} ÷ {divisor} = {values[res]:,.1f}")
            
            min_resource = min(values, key=values.get)
            log.success(f"🎯 Legkevesebb: {min_resource.upper()} ({values[min_resource]:,.1f})")
            
            # 3. Farm indítás
            log.separator('-', 60)
            log.action(f"🌾 {min_resource.upper()} FARMOLÁS INDÍTÁSA")
            log.separator('-', 60)
            
            farm = self.farms.get(min_resource)
            
            if not farm:
                log.error(f"Farm instance nem található: {min_resource}")
                continue
            
            result = farm.run()
            
            if result == "RESTART":
                log.warning("⚠️ Farm restart szükséges, ciklus újraindítása...")
                current_cycle -= 1  # Nem számít bele
                continue
            
            log.success(f"✅ Ciklus {current_cycle}/{self.max_cycles} befejezve!")
        
        log.separator('#', 60)
        log.success(f"🏁 {self.max_cycles} CIKLUS BEFEJEZVE - PROGRAM LEÁLL")
        log.separator('#', 60)


def main():
    """Main entry point"""
    
    # Játék ablak inicializálása
    if not initialize_game_window("BlueStacks"):  # Módosítsd a játék ablak nevére!
        log.error("❌ Játék ablak nem található!")
        log.info("Módosítsd a 'BlueStacks' szöveget a library.py-ban a játék ablak nevére.")
        return
    
    # Farm Manager indítása
    try:
        manager = FarmManager()
        manager.run()
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