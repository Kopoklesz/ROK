"""
Ablakkezelés - játék ablak detektálás és fókuszálás
"""
import time
import ctypes
import win32gui
import win32con
import win32api
from typing import Optional, Tuple

# DPI awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass


class WindowManager:
    """Játék ablak kezelése"""
    
    def __init__(self, window_title_hint: str = ""):
        self.window_handle = None
        self.window_title = None
        self.window_title_hint = window_title_hint
        
    def find_window(self, partial_title: str = None) -> bool:
        """
        Játék ablak keresése
        
        Args:
            partial_title: Ablak cím része (pl. "BlueStacks")
            
        Returns:
            bool: Sikerült-e megtalálni az ablakot
        """
        if partial_title is None:
            partial_title = self.window_title_hint
            
        windows = self._enumerate_windows()
        
        # Automatikus keresés
        for hwnd, title in windows:
            if partial_title.lower() in title.lower():
                self.window_handle = hwnd
                self.window_title = title
                print(f"✅ Játék ablak megtalálva: {title}")
                return True
        
        # Manuális kiválasztás
        print("\n🔍 Elérhető ablakok:")
        for i, (hwnd, title) in enumerate(windows):
            print(f"  {i + 1}. {title}")
        
        try:
            choice = input("\nVálassz ablak számot (vagy Enter a kilépéshez): ").strip()
            if not choice:
                return False
                
            idx = int(choice) - 1
            if 0 <= idx < len(windows):
                self.window_handle = windows[idx][0]
                self.window_title = windows[idx][1]
                print(f"✅ Kiválasztva: {self.window_title}")
                return True
        except ValueError:
            pass
        
        print("❌ Nem található a játék ablak!")
        return False
    
    def focus_window(self) -> bool:
        """Fókusz a játék ablakra"""
        if not self.window_handle:
            print("⚠️ Nincs beállítva ablak handle!")
            return False
        
        try:
            # Visszaállítás minimalizáltból
            win32gui.ShowWindow(self.window_handle, win32con.SW_RESTORE)
            time.sleep(0.1)
            
            # Előtérbe hozás
            win32gui.SetForegroundWindow(self.window_handle)
            time.sleep(0.1)
            
            return True
        except Exception as e:
            print(f"❌ Ablak fókuszálás hiba: {e}")
            return False
    
    def get_window_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Ablak pozíció és méret lekérdezése
        
        Returns:
            (x, y, width, height) vagy None
        """
        if not self.window_handle:
            return None
        
        try:
            rect = win32gui.GetWindowRect(self.window_handle)
            x, y, right, bottom = rect
            return (x, y, right - x, bottom - y)
        except Exception as e:
            print(f"❌ Ablak méret lekérdezés hiba: {e}")
            return None
    
    def get_client_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Ablak belső (client) területének mérete
        """
        if not self.window_handle:
            return None
        
        try:
            rect = win32gui.GetClientRect(self.window_handle)
            return rect
        except Exception as e:
            print(f"❌ Client rect hiba: {e}")
            return None
    
    def is_window_visible(self) -> bool:
        """Ablak látható-e"""
        if not self.window_handle:
            return False
        return win32gui.IsWindowVisible(self.window_handle)
    
    def is_window_foreground(self) -> bool:
        """Ablak előtérben van-e"""
        if not self.window_handle:
            return False
        return win32gui.GetForegroundWindow() == self.window_handle
    
    def _enumerate_windows(self) -> list:
        """Összes látható ablak listázása"""
        windows = []
        
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:  # Csak névvel rendelkező ablakok
                    windows.append((hwnd, title))
            return True
        
        win32gui.EnumWindows(callback, None)
        return windows
    
    def __repr__(self):
        if self.window_handle:
            rect = self.get_window_rect()
            return f"<WindowManager: {self.window_title} @ {rect}>"
        return "<WindowManager: No window>"


# Globális instance (singleton pattern)
_window_manager_instance = None

def get_window_manager(window_title_hint: str = "") -> WindowManager:
    """Globális WindowManager lekérése (singleton)"""
    global _window_manager_instance
    if _window_manager_instance is None:
        _window_manager_instance = WindowManager(window_title_hint)
    return _window_manager_instance


if __name__ == "__main__":
    # Teszt
    wm = WindowManager()
    if wm.find_window("BlueStacks"):
        wm.focus_window()
        print(f"Ablak méret: {wm.get_window_rect()}")