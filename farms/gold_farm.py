"""
Auto Farm - Gold Farm
Arany farmolás specifikus implementáció
"""
from pathlib import Path
from farms.base_farm import BaseFarm


class GoldFarm(BaseFarm):
    """Arany farm"""
    
    def __init__(self):
        config_dir = Path(__file__).parent.parent / 'config'
        super().__init__('gold', config_dir)


if __name__ == "__main__":
    # Teszt
    farm = GoldFarm()
    result = farm.run()
    print(f"Farm eredmény: {result}")