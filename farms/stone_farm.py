"""
Auto Farm - Stone Farm
Kő farmolás specifikus implementáció
"""
from pathlib import Path
from farms.base_farm import BaseFarm


class StoneFarm(BaseFarm):
    """Kő farm"""
    
    def __init__(self):
        config_dir = Path(__file__).parent.parent / 'config'
        super().__init__('stone', config_dir)


if __name__ == "__main__":
    # Teszt
    farm = StoneFarm()
    result = farm.run()
    print(f"Farm eredmény: {result}")