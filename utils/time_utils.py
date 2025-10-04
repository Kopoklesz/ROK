"""
Auto Farm - Time Utils
Idő parsing és formázás: HH:MM:SS ↔ másodperc
"""
import re


def parse_time(ocr_text):
    """
    OCR szövegből időt parse-ol
    
    Támogatott formátumok:
    - "01:05:30" → 3930 sec
    - "1:5:30" → 3930 sec
    - "00:05:00" → 300 sec
    
    Args:
        ocr_text: OCR-ből kiolvasott idő szöveg
        
    Returns:
        int: Másodpercek vagy None hiba esetén
    """
    try:
        # Tisztítás
        text = ocr_text.strip()
        
        # Csak számok és kettőspont megtartása
        text = re.sub(r'[^0-9:]', '', text)
        
        # Split kettőspontokra
        parts = text.split(':')
        
        if len(parts) == 3:
            # HH:MM:SS formátum
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return total_seconds
        
        elif len(parts) == 2:
            # MM:SS formátum (órák nélkül)
            minutes = int(parts[0])
            seconds = int(parts[1])
            
            total_seconds = minutes * 60 + seconds
            return total_seconds
        
        else:
            return None
    
    except Exception as e:
        print(f"Time parse hiba: {ocr_text} → {e}")
        return None


def format_time(seconds):
    """
    Másodperc → HH:MM:SS formátum
    
    Args:
        seconds: Másodpercek száma
        
    Returns:
        str: Formázott idő (pl. "01:05:30")
    """
    try:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    except:
        return "00:00:00"


def add_times(time_a_sec, time_b_sec):
    """
    Két időpont összeadása
    
    Args:
        time_a_sec: Első idő másodpercben
        time_b_sec: Második idő másodpercben
        
    Returns:
        int: Összeg másodpercben
    """
    return time_a_sec + time_b_sec


# Tesztek
if __name__ == "__main__":
    print("Time Utils Tesztek:\n")
    
    # Parse tesztek
    test_cases = [
        ("01:05:30", 3930),
        ("1:5:30", 3930),
        ("00:05:00", 300),
        ("10:00", 600),
        ("02:30:45", 9045),
    ]
    
    print("Parse tesztek:")
    for input_text, expected in test_cases:
        result = parse_time(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_text}' → {result} sec (várt: {expected} sec)")
    
    # Format tesztek
    print("\nFormat tesztek:")
    format_tests = [
        (3930, "01:05:30"),
        (300, "00:05:00"),
        (9045, "02:30:45"),
    ]
    
    for seconds, expected in format_tests:
        result = format_time(seconds)
        status = "✅" if result == expected else "❌"
        print(f"{status} {seconds} sec → '{result}' (várt: '{expected}')")