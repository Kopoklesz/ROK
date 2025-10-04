"""
Auto Farm - Wheat Farm
Búza farmolás specifikus implementáció
"""
from pathlib import Path
from farms.base_farm import BaseFarm


class WheatFarm(BaseFarm):
    """Búza farm"""
    
    def __init__(self):
        config_dir = Path(__file__).parent.parent / 'config'
        super().__init__('wheat', config_dir)


if __name__ == "__main__":
    # Teszt
    farm = WheatFarm()
    result = farm.run()
    print(f"Farm eredmény: {result}")