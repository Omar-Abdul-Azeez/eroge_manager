# -*- encoding:utf-8 -*-
from trackers import *
from . import parse_skip_str, read_dump, infer_dump, clean_dump, merge_dump, diff, write_structure, Modes
from . import helper


def main():
    skip_str = ''
    skip = parse_skip_str(skip_str)

    if Trackers.EGS in AVAILABLE and not bool(helper.ask('Use EGS? empty for Y anything for N')):
        cdmp_egs = read_dump(Trackers.EGS, can_dl=True)
        pdmp_egs = read_dump(Trackers.EGS, none=True)
        if pdmp_egs is None:
            pdmp_egs = infer_dump(Trackers.EGS)
        clean_dump(Trackers.EGS, cdmp_egs)
        clean_dump(Trackers.EGS, pdmp_egs)
    else:
        cdmp_egs = None
        pdmp_egs = None

    cv_path = None
    if Trackers.VNDB in AVAILABLE and bool(helper.ask('Use VNDB? empty for N anything for Y')):
        cdmp_vndb = read_dump(Trackers.VNDB, can_dl=True)
        pdmp_vndb = read_dump(Trackers.VNDB, none=True)
        if pdmp_vndb is None:
            pdmp_vndb = infer_dump(Trackers.VNDB)
        clean_dump(Trackers.VNDB, cdmp_vndb)
        clean_dump(Trackers.VNDB, pdmp_vndb)
        if not bool(helper.ask('Create icons for folders? empty for Y anything for N')):
            cv_path = helper.ask('VNDB covers dump path: leave empty to download covers')
            if not cv_path:
                cv_path = None
    else:
        cdmp_vndb = None
        pdmp_vndb = None

    if cdmp_egs is not None and cdmp_vndb is not None:
        cdmp_egs = merge_dump(cdmp_egs, cdmp_vndb)
        if pdmp_egs is not None and pdmp_vndb is not None:
            pdmp_egs = merge_dump(pdmp_egs, pdmp_vndb)
        else:
            pdmp_egs = infer_dump(Trackers.EGS_VNDB)
    elif cdmp_egs is not None:
        cdmp_egs = cdmp_egs
        if pdmp_egs is not None:
            pdmp_egs = pdmp_egs
        else:
            pdmp_egs = infer_dump(Trackers.EGS)
    elif cdmp_vndb is not None:
        cdmp_egs = cdmp_vndb
        if pdmp_vndb is not None:
            pdmp_egs = pdmp_vndb
        else:
            pdmp_egs = infer_dump(Trackers.VNDB)
    else:
        print('Requires either EGS or VNDB. Please provide.')
        input()
        return

    diff_dmp = diff(pdmp_egs, cdmp_egs)
    write_structure(diff_dmp, Modes.DRYRUN, skip=skip, cv_path=cv_path)
    input()
    write_structure(diff_dmp, Modes.NORMAL, skip=skip, cv_path=cv_path)
    input()
