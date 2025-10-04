"""
Auto Farm - Coordinate Helper
Kattintásra koordináta kiírás segédeszköz
"""
from pynput import mouse, keyboard


class CoordinateHelper:
    """Kattintásra koordináta kiírás"""
    
    def __init__(self):
        self.coordinates = []
        self.running = True
    
    def on_click(self, x, y, button, pressed):
        """Egér kattintás esemény"""
        if pressed and button == mouse.Button.left:
            print(f"\n🖱️  Koordináta: ({x}, {y})")
            self.coordinates.append((x, y))
    
    def on_press(self, key):
        """Billentyű lenyomás esemény"""
        try:
            if key == keyboard.Key.esc:
                print("\n\n⏹️  ESC lenyomva - Kilépés")
                self.running = False
                return False
        except:
            pass
    
    def run(self):
        """Fő ciklus"""
        print("="*60)
        print("🖱️  KOORDINÁTA HELPER")
        print("="*60)
        print("\nHasználat:")
        print("  - Kattints bárhova → koordináta kiírás")
        print("  - ESC → kilépés")
        print("\nVárakozás kattintásokra...\n")
        print("="*60)
        
        # Listeners indítása
        mouse_listener = mouse.Listener(on_click=self.on_click)
        keyboard_listener = keyboard.Listener(on_press=self.on_press)
        
        mouse_listener.start()
        keyboard_listener.start()
        
        # Várakozás kilépésig
        keyboard_listener.join()
        mouse_listener.stop()
        
        # Összegzés
        print("\n" + "="*60)
        print("📊 ÖSSZEGZÉS")
        print("="*60)
        print(f"\nÖsszesen {len(self.coordinates)} koordináta gyűjtve:\n")
        for i, (x, y) in enumerate(self.coordinates, 1):
            print(f"  {i}. ({x}, {y})")
        print("\n" + "="*60)


def main():
    """Main entry point"""
    helper = CoordinateHelper()
    helper.run()


if __name__ == "__main__":
    main()