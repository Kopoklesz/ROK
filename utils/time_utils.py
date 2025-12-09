"""
Auto Farm - Time Utils
Idő parsing és formázás: HH:MM:SS ↔ másodperc
JAVÍTOTT VERZIÓ - "Gathering Time: 01:13:48" formátum kezelése
"""
import re


def parse_time(ocr_text):
    """
    OCR szövegből időt parse-ol

    Támogatott formátumok:
    - "Gathering Time: 01:13:48" → 4428 sec
    - "01:05:30" → 3930 sec
    - "1:5:30" → 3930 sec
    - "00:05:00" → 300 sec
    - "Idle" / "idle" / "Idl" / "ldle" → None (idle állapot)
    - Ha nem idő és nem idle → 0 sec (completed, restart futhat)

    Args:
        ocr_text: OCR-ből kiolvasott idő szöveg

    Returns:
        int: Másodpercek, 0 ha completed, None ha idle vagy hiba
    """
    try:
        # Tisztítás
        text = ocr_text.strip()
        text_lower = text.lower().replace(' ', '').replace('-', '').replace('_', '')

        # ======= 1. IDLE FELISMERÉS (PRIORITÁS!) =======
        # Az Idle-t általában jól felismeri az OCR
        # Lehetséges OCR hibák: "Idle", "idle", "Idl", "ldle", "Id1e", "1dle"
        idle_patterns = [
            'idle', 'idl', 'ldle', 'idie', 'id1e', '1dle', 'idel', 'idlee'
        ]

        if any(pattern in text_lower for pattern in idle_patterns):
            # Ha idle-t találunk, azonnal visszatérünk None-nal
            return None
        # ===============================================

        # ======= 2. IDŐ FORMÁTUM PARSE =======
        # Az időt általában jól felismeri az OCR
        # Próbáljuk meg időként parse-olni

        # PREFIX ELTÁVOLÍTÁS (ha van "Gathering Time:" vagy hasonló)
        time_text = text
        if ':' in text:
            parts = text.split()
            for part in reversed(parts):
                if part.count(':') >= 1:
                    time_text = part
                    break

        # Csak számok és kettőspont megtartása
        time_clean = re.sub(r'[^0-9:]', '', time_text)

        # Split kettőspontokra
        time_parts = time_clean.split(':')

        if len(time_parts) == 3:
            # HH:MM:SS formátum
            hours = int(time_parts[0])
            minutes = int(time_parts[1])
            seconds = int(time_parts[2])

            total_seconds = hours * 3600 + minutes * 60 + seconds
            return total_seconds

        elif len(time_parts) == 2:
            # MM:SS formátum
            minutes = int(time_parts[0])
            seconds = int(time_parts[1])

            total_seconds = minutes * 60 + seconds
            return total_seconds
        # ======================================

        # ======= 3. COMPLETED FELISMERÉS (FALLBACK) =======
        # Ha nem idle ÉS nem tudtuk időként parse-olni
        # → akkor completed (gyűjtés kész, restart futhat)
        #
        # Lehetséges OCR hibák:
        # "Completed", "Com pleted", "Comp leted", "ed", "ompleted", stb.

        # Explicit completed szavak
        completed_patterns = [
            'completed', 'complted', 'complet', 'ompleted',
            'compled', 'compleed', 'compeled'
        ]

        if any(pattern in text_lower for pattern in completed_patterns):
            return 0

        # Részleges match-ek
        has_beginning = any(part in text_lower for part in ['compl', 'comp', 'omp', 'mpl'])
        has_ending = any(part in text_lower for part in ['eted', 'leted', 'ted', 'eted'])

        if has_beginning and has_ending:
            return 0

        # Nagyon rövid szöveg (valószínűleg "ed" vagy hasonló)
        if len(text_lower) <= 3 and any(part in text_lower for part in ['ed', 'd', 'e']):
            return 0

        # ===== ÚJ: Ha semmi nem illeszkedett, de nem idle =====
        # → valószínűleg completed, de rosszul olvasva
        # Visszaadunk 0-t (restart futhat)
        return 0
        # ===================================================

    except Exception as e:
        print(f"Time parse hiba: {ocr_text} → {e}")
        # Hiba esetén is 0-t adunk vissza (inkább restart mint hibás idő)
        return 0


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
    print("Time Utils Tesztek (ÚJ LOGIKA - Idle → None, Completed → 0):\n")

    # Parse tesztek
    test_cases = [
        # ===== IDŐ FORMÁTUMOK (jól felismert) =====
        ("01:05:30", 3930),
        ("1:5:30", 3930),
        ("00:05:00", 300),
        ("10:00", 600),
        ("02:30:45", 9045),
        ("Gathering Time: 01:13:48", 4428),
        ("Gathering Time: 00:05:00", 300),
        ("March Time: 01:05:30", 3930),

        # ===== IDLE FELISMERÉS (visszatér: None) =====
        ("Idle", None),
        ("idle", None),
        ("Idl", None),
        ("ldle", None),
        ("Id1e", None),
        ("1dle", None),
        ("Idel", None),

        # ===== COMPLETED FELISMERÉS (visszatér: 0) =====
        ("Completed", 0),
        ("completed", 0),
        ("Com pleted", 0),
        ("Comp leted", 0),
        ("ed", 0),
        ("ompleted", 0),
        ("complted", 0),
        ("Complet", 0),
        ("mpleted", 0),

        # ===== FALLBACK: Ha nem idő és nem idle → 0 (restart) =====
        ("asdfsdf", 0),  # Random szemét → completed (restart)
        ("xyz", 0),       # Random szöveg → completed
        ("123", 0),       # Csak számok, de nem idő formátum → completed
    ]

    print("Parse tesztek:")
    for input_text, expected in test_cases:
        result = parse_time(input_text)
        status = "✅" if result == expected else "❌"
        expected_str = "None" if expected is None else f"{expected} sec"
        result_str = "None" if result is None else f"{result} sec"
        print(f"{status} '{input_text}' → {result_str} (várt: {expected_str})")

    # Format tesztek
    print("\nFormat tesztek:")
    format_tests = [
        (3930, "01:05:30"),
        (300, "00:05:00"),
        (9045, "02:30:45"),
        (4428, "01:13:48"),
        (0, "00:00:00"),
    ]

    for seconds, expected in format_tests:
        result = format_time(seconds)
        status = "✅" if result == expected else "❌"
        print(f"{status} {seconds} sec → '{result}' (várt: '{expected}')")