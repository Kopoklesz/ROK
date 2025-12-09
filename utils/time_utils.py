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
    - "Completed" / "Com pleted" / "ed" → 0 sec (gyűjtés kész)

    Args:
        ocr_text: OCR-ből kiolvasott idő szöveg

    Returns:
        int: Másodpercek vagy None hiba esetén
    """
    try:
        # Tisztítás
        text = ocr_text.strip()

        # ======= ÚJ: "COMPLETED" FELISMERÉS =======
        # OCR sokszor rosszul olvassa: "Com pleted", "ed", "ompleted", stb.
        # Ha "completed"-et detektálunk → 0 sec (gyűjtés kész)
        text_lower = text.lower().replace(' ', '').replace('-', '')

        # 1. Teljes "completed" vagy közel van hozzá
        if 'completed' in text_lower or 'complted' in text_lower or 'complet' in text_lower:
            return 0

        # 2. RészlegesMatch-ek (OCR hibák):
        #    - Tartalmazza "compl" vagy "comp" vagy "omp" vagy "mpl" ÉS
        #    - Tartalmazza "eted" vagy "leted" vagy "ted" vagy csak "ed"
        has_beginning = any(part in text_lower for part in ['compl', 'comp', 'omp', 'mpl'])
        has_ending = any(part in text_lower for part in ['eted', 'leted', 'ted'])

        # 3. Nagyon rövid szöveg, ami csak "ed" vagy "d" (gyakori OCR hiba)
        very_short = len(text_lower) <= 3 and ('ed' in text_lower or text_lower == 'd')

        # 4. KIZÁRÁS: Ne keverje össze az "idle"-lel!
        is_idle = 'idle' in text_lower or 'idl' in text_lower

        if not is_idle and (has_beginning and has_ending or very_short):
            return 0
        # ==========================================

        # ======= PREFIX ELTÁVOLÍTÁS =======
        # Ha van "Gathering Time:" vagy hasonló prefix, vágjuk le
        if ':' in text:
            # Keressük meg a HH:MM:SS formátumot a szövegben
            # Split szóközökre és keressük az időformátumot
            parts = text.split()

            for part in reversed(parts):  # Hátulról nézzük (utolsó elem az idő)
                # Ha legalább 2 kettőspont van benne → HH:MM:SS vagy MM:SS
                if part.count(':') >= 1:
                    text = part
                    break
        # ======================================

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
    print("Time Utils Tesztek (JAVÍTOTT VERZIÓ - COMPLETED FELISMERÉS):\n")

    # Parse tesztek
    test_cases = [
        # Régi formátumok
        ("01:05:30", 3930),
        ("1:5:30", 3930),
        ("00:05:00", 300),
        ("10:00", 600),
        ("02:30:45", 9045),

        # Gathering Time formátumok
        ("Gathering Time: 01:13:48", 4428),
        ("Gathering Time: 00:05:00", 300),
        ("March Time: 01:05:30", 3930),

        # ÚJ: COMPLETED felismerés (OCR hibák)
        ("Completed", 0),
        ("completed", 0),
        ("Com pleted", 0),
        ("Comp leted", 0),
        ("ed", 0),
        ("ompleted", 0),
        ("complted", 0),
        ("Complet", 0),
        ("mpleted", 0),

        # KIZÁRÁS: Idle ne legyen completed!
        # ("Idle", None),  # Ez None-t kell adjon, mert nem idő és nem completed
        # ("idle", None),
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
        (4428, "01:13:48"),
        (0, "00:00:00"),
    ]

    for seconds, expected in format_tests:
        result = format_time(seconds)
        status = "✅" if result == expected else "❌"
        print(f"{status} {seconds} sec → '{result}' (várt: '{expected}')")