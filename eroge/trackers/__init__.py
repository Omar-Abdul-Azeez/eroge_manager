# -*- encoding:utf-8 -*-
from os import path
import importlib
from eroge.helper import *
import eroge.trackers.rules as rules

__trackers_dir = path.dirname(__file__)
TRACKERS = dict()
walkie = walklevel(__trackers_dir, depth=2)
next(walkie)
for mdl, _, _ in walkie:
    nm = path.basename(mdl)
    if nm == '__pycache__':
        continue
    TRACKERS[nm] = importlib.import_module('.' + nm, package='eroge.trackers')


def get_tracker():
    if len(TRACKERS) == 0:
        raise ModuleNotFoundError
    return ask("Choose tracker:", choices=list(TRACKERS.keys()), show=True)
