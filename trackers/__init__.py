# -*- encoding:utf-8 -*-
from enum import Enum


class Trackers(Enum):
    EGS = 'egs'
    VNDB = 'vndb'


AVAILABLE = set()

try:
    import egs
    AVAILABLE.add(Trackers.EGS)
except ImportError:
    pass

try:
    import vndb
    AVAILABLE.add(Trackers.VNDB)
except ImportError:
    pass
