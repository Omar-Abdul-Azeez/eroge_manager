# -*- encoding:utf-8 -*-
from . import write_dump
from . import helper


def main():
    user = helper.ask('user:')
    root = helper.ask('root: (leave blank for current directory)')
    if root == '':
        root = '.'
    full_backup = bool(helper.ask('Dump entire userlist? Empty for N anything for Y'))
    write_dump(user=user, full_backup=full_backup, root=root)
