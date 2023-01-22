# -*- encoding:utf-8 -*-
from eroge import *
from eroge.helper import ask


def main():
    skip_str = ''
    skip = parse_skip_str(skip_str)
    dump_root = ask('Dump root:')
    backlog_root = ask('Backlog root:')
    pdmp, cdmp = get_dumps(dump_root, backlog_root)
    sync_backlog(pdmp, cdmp, Modes.DRYRUN, backlog_root=backlog_root, skip=skip)
    input()
    sync_backlog(pdmp, cdmp, Modes.NORMAL, backlog_root=backlog_root, skip=skip)
    input()
