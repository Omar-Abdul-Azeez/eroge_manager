from enum import Enum


class Types(Enum):
    EGS = 'egs'
    VNDB = 'vndb'
    EGS_VNDB = 'egs + vndb'


class Modes(Enum):
    NORMAL = 'normal'
    DRYRUN = 'dryrun'
