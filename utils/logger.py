"""
Auto Farm - Logger
Színes, részletes logging minden művelethez
"""
from datetime import datetime


class FarmLogger:
    """Részletes logging rendszer"""
    
    COLORS = {
        'RESET': '\033[0m',
        'BLUE': '\033[94m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'RED': '\033[91m',
        'CYAN': '\033[96m',
        'MAGENTA': '\033[95m',
        'WHITE': '\033[97m'
    }
    
    @staticmethod
    def _timestamp():
        """Időbélyeg generálás"""
        return datetime.now().strftime("%H:%M:%S")
    
    @staticmethod
    def _color(text, color):
        """Színes szöveg (opcionális)"""
        try:
            return f"{FarmLogger.COLORS[color]}{text}{FarmLogger.COLORS['RESET']}"
        except:
            return text
    
    @staticmethod
    def info(message):
        """Általános információ (kék)"""
        timestamp = FarmLogger._timestamp()
        print(f"[{timestamp}] ℹ️  {FarmLogger._color(message, 'BLUE')}")
    
    @staticmethod
    def success(message):
        """Sikeres művelet (zöld)"""
        timestamp = FarmLogger._timestamp()
        print(f"[{timestamp}] ✅ {FarmLogger._color(message, 'GREEN')}")
    
    @staticmethod
    def warning(message):
        """Figyelmeztetés (sárga)"""
        timestamp = FarmLogger._timestamp()
        print(f"[{timestamp}] ⚠️  {FarmLogger._color(message, 'YELLOW')}")
    
    @staticmethod
    def error(message):
        """Hiba (piros)"""
        timestamp = FarmLogger._timestamp()
        print(f"[{timestamp}] ❌ {FarmLogger._color(message, 'RED')}")
    
    @staticmethod
    def action(message):
        """Akció végrehajtás (cián)"""
        timestamp = FarmLogger._timestamp()
        print(f"[{timestamp}] 🎬 {FarmLogger._color(message, 'CYAN')}")
    
    @staticmethod
    def wait(message):
        """Várakozás (magenta)"""
        timestamp = FarmLogger._timestamp()
        print(f"[{timestamp}] ⏳ {FarmLogger._color(message, 'MAGENTA')}")
    
    @staticmethod
    def ocr(message):
        """OCR olvasás"""
        timestamp = FarmLogger._timestamp()
        print(f"[{timestamp}] 📖 {message}")
    
    @staticmethod
    def click(message):
        """Kattintás"""
        timestamp = FarmLogger._timestamp()
        print(f"[{timestamp}] 🖱️  {message}")
    
    @staticmethod
    def search(message):
        """Keresés"""
        timestamp = FarmLogger._timestamp()
        print(f"[{timestamp}] 🔍 {message}")
    
    @staticmethod
    def separator(char='=', length=60):
        """Elválasztó vonal"""
        print(char * length)