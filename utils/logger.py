"""
Auto Farm - Logger
Színes, részletes logging minden művelethez + File logging + Log rotáció
MÓDOSÍTVA: Mozgás tracking (click, action, search) Anti-AFK számára
"""
from datetime import datetime
from pathlib import Path
import threading


class FarmLogger:
    """Részletes logging rendszer file logging-gal + movement tracking"""
    
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
    
    # Class változók (singleton-hoz)
    _log_file = None
    _log_lock = threading.Lock()
    _last_log_time = None
    _last_movement_time = None  # ✅ ÚJ: Utolsó mozgás ideje (click/action/search)
    _logs_dir = None
    
    @classmethod
    def initialize(cls, logs_dir=None):
        """
        Logger inicializálás file logging-gal
        
        Args:
            logs_dir: Logs könyvtár path (None = auto)
        """
        if logs_dir is None:
            logs_dir = Path(__file__).parent.parent / 'logs'
        
        cls._logs_dir = Path(logs_dir)
        cls._logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Log fájl név generálás
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"farm_{timestamp}.log"
        log_path = cls._logs_dir / log_filename
        
        # Fájl megnyitása
        try:
            cls._log_file = open(log_path, 'w', encoding='utf-8')
            cls.info(f"Logger inicializálva: {log_path}")
        except Exception as e:
            print(f"Logger init hiba: {e}")
        
        # Log rotáció (max 10 fájl)
        cls._rotate_logs()
    
    @classmethod
    def close(cls):
        """Logger bezárása (graceful shutdown)"""
        if cls._log_file:
            cls._log_file.close()
            cls._log_file = None
    
    @classmethod
    def _rotate_logs(cls, max_files=10):
        """
        Log rotáció - max 10 fájl megtartása
        
        Args:
            max_files: Maximum fájlok száma
        """
        try:
            if not cls._logs_dir:
                return
            
            # Összes log fájl listázása
            log_files = sorted(cls._logs_dir.glob('farm_*.log'))
            
            # Ha több mint max_files
            if len(log_files) > max_files:
                # Legrégebbiek törlése
                for old_file in log_files[:-max_files]:
                    old_file.unlink()
                    print(f"Régi log törölve: {old_file.name}")
        
        except Exception as e:
            print(f"Log rotáció hiba: {e}")
    
    @classmethod
    def _write_to_file(cls, message):
        """
        Fájlba írás (thread-safe)
        
        Args:
            message: Log üzenet
        """
        with cls._log_lock:
            if cls._log_file:
                try:
                    cls._log_file.write(message + '\n')
                    cls._log_file.flush()  # Azonnali írás
                except:
                    pass
    
    @classmethod
    def register_movement(cls):
        """
        ✅ ÚJ: Mozgás regisztrálása (click, action, search)
        Anti-AFK idle detection használja
        """
        cls._last_movement_time = datetime.now()
    
    @classmethod
    def get_last_movement_time(cls):
        """
        ✅ ÚJ: Utolsó mozgás időpontja
        
        Returns:
            datetime: Utolsó mozgás vagy None
        """
        return cls._last_movement_time
    
    @staticmethod
    def _timestamp():
        """Időbélyeg generálás"""
        FarmLogger._last_log_time = datetime.now()
        return FarmLogger._last_log_time.strftime("%H:%M:%S")
    
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
        colored_msg = f"[{timestamp}] ℹ️  {FarmLogger._color(message, 'BLUE')}"
        plain_msg = f"[{timestamp}] ℹ️  {message}"
        
        print(colored_msg)
        FarmLogger._write_to_file(plain_msg)
    
    @staticmethod
    def success(message):
        """Sikeres művelet (zöld)"""
        timestamp = FarmLogger._timestamp()
        colored_msg = f"[{timestamp}] ✅ {FarmLogger._color(message, 'GREEN')}"
        plain_msg = f"[{timestamp}] ✅ {message}"
        
        print(colored_msg)
        FarmLogger._write_to_file(plain_msg)
    
    @staticmethod
    def warning(message):
        """Figyelmeztetés (sárga)"""
        timestamp = FarmLogger._timestamp()
        colored_msg = f"[{timestamp}] ⚠️  {FarmLogger._color(message, 'YELLOW')}"
        plain_msg = f"[{timestamp}] ⚠️  {message}"
        
        print(colored_msg)
        FarmLogger._write_to_file(plain_msg)
    
    @staticmethod
    def error(message):
        """Hiba (piros)"""
        timestamp = FarmLogger._timestamp()
        colored_msg = f"[{timestamp}] ❌ {FarmLogger._color(message, 'RED')}"
        plain_msg = f"[{timestamp}] ❌ {message}"
        
        print(colored_msg)
        FarmLogger._write_to_file(plain_msg)
    
    @staticmethod
    def action(message):
        """Akció végrehajtás (cián) - ✅ MOZGÁS"""
        FarmLogger.register_movement()  # ✅ Mozgás regisztrálása
        
        timestamp = FarmLogger._timestamp()
        colored_msg = f"[{timestamp}] 🎬 {FarmLogger._color(message, 'CYAN')}"
        plain_msg = f"[{timestamp}] 🎬 {message}"
        
        print(colored_msg)
        FarmLogger._write_to_file(plain_msg)
    
    @staticmethod
    def wait(message):
        """Várakozás (magenta)"""
        timestamp = FarmLogger._timestamp()
        colored_msg = f"[{timestamp}] ⏳ {FarmLogger._color(message, 'MAGENTA')}"
        plain_msg = f"[{timestamp}] ⏳ {message}"
        
        print(colored_msg)
        FarmLogger._write_to_file(plain_msg)
    
    @staticmethod
    def ocr(message):
        """OCR olvasás"""
        timestamp = FarmLogger._timestamp()
        msg = f"[{timestamp}] 📖 {message}"
        
        print(msg)
        FarmLogger._write_to_file(msg)
    
    @staticmethod
    def click(message):
        """Kattintás - ✅ MOZGÁS"""
        FarmLogger.register_movement()  # ✅ Mozgás regisztrálása
        
        timestamp = FarmLogger._timestamp()
        msg = f"[{timestamp}] 🖱️  {message}"
        
        print(msg)
        FarmLogger._write_to_file(msg)
    
    @staticmethod
    def search(message):
        """Keresés - ✅ MOZGÁS"""
        FarmLogger.register_movement()  # ✅ Mozgás regisztrálása
        
        timestamp = FarmLogger._timestamp()
        msg = f"[{timestamp}] 🔍 {message}"
        
        print(msg)
        FarmLogger._write_to_file(msg)
    
    @staticmethod
    def separator(char='=', length=60):
        """Elválasztó vonal"""
        line = char * length
        print(line)
        FarmLogger._write_to_file(line)
    
    @staticmethod
    def get_last_log_time():
        """
        Utolsó log timestamp lekérése (backward compatibility)
        
        Returns:
            datetime: Utolsó log időpontja vagy None
        """
        return FarmLogger._last_log_time