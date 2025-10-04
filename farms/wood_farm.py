"""
Auto Farm - Wood Farm
Fa farmolás specifikus implementáció
"""
from pathlib import Path
from farms.base_farm import BaseFarm


class WoodFarm(BaseFarm):
    """Fa farm"""
    
    def __init__(self):
        config_dir = Path(__file__).parent.parent / 'config'
        super().__init__('wood', config_dir)


if __name__ == "__main__":
    # Teszt
    farm = WoodFarm()
    result = farm.run()
    print(f"Farm eredmény: {result}")