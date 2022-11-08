# -*- encoding:utf-8 -*-
from . import write_dump, ask_table
from . import helper


def main():
    user = helper.ask('user:')
    root = helper.ask('root: (leave blank for current directory)')
    if root == '':
        root = '.'
    table = ask_table()
    write_dump(user=user, table=table, root=root)
