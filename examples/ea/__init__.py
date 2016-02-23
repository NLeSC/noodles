from noodles import serial
from .chromosome import Chromosome
from .generation import Generation
from .rastrigin import Rastrigin
from .ea import EA


def registry():
    return serial.pickle() + serial.base()

__all__ = [
    'Chromosome',
    'Generation',
    'Rastrigin',
    'registry',
    'EA'
]
