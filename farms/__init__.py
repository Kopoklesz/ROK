"""
Auto Farm - Farms Package
"""
from .base_farm import BaseFarm
from .wheat_farm import WheatFarm
from .wood_farm import WoodFarm
from .stone_farm import StoneFarm
from .gold_farm import GoldFarm

__all__ = [
    'BaseFarm',
    'WheatFarm',
    'WoodFarm',
    'StoneFarm',
    'GoldFarm'
]