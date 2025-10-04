"""
Auto Farm - OCR Parser
ROK erőforrás formátumok parse-olása: 1.2M, 100.0K, 99,000
"""
import re


def parse_resource_value(ocr_text):
    """
    Parse ROK erőforrás formátumokat
    
    Támogatott formátumok:
    - "1.2M" → 1,200,000
    - "100.0K" → 100,000
    - "99,000" → 99,000
    - "500" → 500
    
    Args:
        ocr_text: OCR-ből kiolvasott szöveg
        
    Returns:
        int: Parse-olt érték vagy 0 hiba esetén
    """
    try:
        # Tisztítás
        text = ocr_text.strip().upper()
        text = text.replace(',', '')  # Vesszők eltávolítása
        text = text.replace(' ', '')  # Szóközök eltávolítása
        
        # Millió (M)
        if 'M' in text:
            number_str = text.replace('M', '')
            number = float(number_str)
            return int(number * 1_000_000)
        
        # Ezer (K)
        elif 'K' in text:
            number_str = text.replace('K', '')
            number = float(number_str)
            return int(number * 1_000)
        
        # Sima szám
        else:
            # Csak számjegyek megtartása
            number_str = re.sub(r'[^0-9.]', '', text)
            if number_str:
                return int(float(number_str))
            else:
                return 0
    
    except Exception as e:
        print(f"Parse hiba: {ocr_text} → {e}")
        return 0


# Tesztek
if __name__ == "__main__":
    test_cases = [
        ("1.2M", 1_200_000),
        ("100.0K", 100_000),
        ("99,000", 99_000),
        ("500", 500),
        ("2.5M", 2_500_000),
        ("750.5K", 750_500),
    ]
    
    print("OCR Parser Tesztek:\n")
    for input_text, expected in test_cases:
        result = parse_resource_value(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_text}' → {result:,} (várt: {expected:,})")