"""
Auto Farm - Region Selector
Egérrel tartomány kijelölés segédeszköz
"""
import cv2
import numpy as np
from PIL import ImageGrab


class RegionSelector:
    """Tartomány kijelölés GUI-val"""
    
    def __init__(self):
        self.start_point = None
        self.end_point = None
        self.selecting = False
        self.screenshot = None
    
    def select_region(self, title="Jelöld ki a területet"):
        """
        Interaktív tartomány kijelölés
        
        Returns:
            dict: {'x': x, 'y': y, 'width': w, 'height': h} vagy None
        """
        # Screenshot
        screen = ImageGrab.grab()
        self.screenshot = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        clone = self.screenshot.copy()
        
        window_name = f"{title} (ENTER=mentés, ESC=mégsem)"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, clone)
        
        # Mouse callback
        def mouse_callback(event, x, y, flags, param):
            nonlocal clone
            
            if event == cv2.EVENT_LBUTTONDOWN:
                self.start_point = (x, y)
                self.selecting = True
            
            elif event == cv2.EVENT_MOUSEMOVE and self.selecting:
                clone = self.screenshot.copy()
                cv2.rectangle(clone, self.start_point, (x, y), (0, 255, 0), 2)
                
                # Méret kiírás
                w = abs(x - self.start_point[0])
                h = abs(y - self.start_point[1])
                cv2.putText(clone, f"{w}x{h}", (x + 10, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow(window_name, clone)
            
            elif event == cv2.EVENT_LBUTTONUP:
                self.end_point = (x, y)
                self.selecting = False
                cv2.rectangle(clone, self.start_point, self.end_point, (0, 255, 0), 2)
                cv2.imshow(window_name, clone)
        
        cv2.setMouseCallback(window_name, mouse_callback)
        
        # Várakozás ENTER vagy ESC-re
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == 13:  # ENTER
                cv2.destroyWindow(window_name)
                
                if self.start_point and self.end_point:
                    x1, y1 = self.start_point
                    x2, y2 = self.end_point
                    
                    x = min(x1, x2)
                    y = min(y1, y2)
                    w = abs(x2 - x1)
                    h = abs(y2 - y1)
                    
                    return {'x': x, 'y': y, 'width': w, 'height': h}
                else:
                    return None
            
            elif key == 27:  # ESC
                cv2.destroyWindow(window_name)
                return None

    def select_point(self, title="Kattints egy pontra"):
        """
        Interaktív pont kijelölés (egyetlen kattintás)

        Returns:
            list: [x, y] vagy None
        """
        # Screenshot
        screen = ImageGrab.grab()
        self.screenshot = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        clone = self.screenshot.copy()

        window_name = f"{title} (KATTINTS egyszer, ENTER=mentés, ESC=mégsem)"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, clone)

        selected_point = None

        # Mouse callback
        def mouse_callback(event, x, y, flags, param):
            nonlocal clone, selected_point

            if event == cv2.EVENT_LBUTTONDOWN:
                selected_point = [x, y]

                # Rajzolás
                clone = self.screenshot.copy()
                cv2.circle(clone, (x, y), 10, (0, 255, 0), 2)
                cv2.drawMarker(clone, (x, y), (0, 255, 0), cv2.MARKER_CROSS, 20, 2)

                # Koordináta kiírás
                cv2.putText(clone, f"({x}, {y})", (x + 15, y - 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                cv2.imshow(window_name, clone)

        cv2.setMouseCallback(window_name, mouse_callback)

        # Várakozás ENTER vagy ESC-re
        while True:
            key = cv2.waitKey(1) & 0xFF

            if key == 13:  # ENTER
                cv2.destroyWindow(window_name)
                return selected_point

            elif key == 27:  # ESC
                cv2.destroyWindow(window_name)
                return None


def main():
    """Test"""
    print("="*60)
    print("📐 REGION SELECTOR TESZT")
    print("="*60)
    print("\nJelöld ki egy területet egérrel!")
    print("  - Húzd végig az egeret")
    print("  - ENTER = mentés")
    print("  - ESC = mégsem")
    print("\n" + "="*60)
    
    selector = RegionSelector()
    region = selector.select_region("Teszt terület")
    
    if region:
        print(f"\n✅ Kijelölt terület:")
        print(f"   x: {region['x']}")
        print(f"   y: {region['y']}")
        print(f"   width: {region['width']}")
        print(f"   height: {region['height']}")
    else:
        print("\n❌ Nincs kijelölés")


if __name__ == "__main__":
    main()