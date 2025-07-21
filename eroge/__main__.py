# -*- encoding:utf-8 -*-
import shlex
import sys
from sys import argv
from argparse import ArgumentParser, ArgumentError
import logging
from configparser import ConfigParser

from eroge import *


config = ConfigParser()
config.read('config.ini')
if config.has_section('logging'):
    section = config['logging']
    level = section.get('level', 'INFO')
    if level == 'INFO':
        level = logging.INFO
    elif level == 'DEBUG':
        level = logging.DEBUG
else:
    level = logging.INFO

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler_file = logging.FileHandler('eroge.log', encoding='utf-8')
handler_file.setFormatter(formatter)
logger = logging.getLogger('eroge')
logger.addHandler(handler_file)
logger.setLevel(level)

formatter_stderr = logging.Formatter('%(levelname)s - %(message)s')
handler_stderr = logging.StreamHandler(sys.stderr)
handler_stderr.setFormatter(formatter_stderr)
handler_stderr.setLevel(logging.WARNING)
logger.addHandler(handler_stderr)


def main():
    parser = ArgumentParser(exit_on_error=False)
    subparsers = parser.add_subparsers(help='Eroge library manager. Helps keep library in a uniform structure. Structure used: [brand]\\[game]')
    library = subparsers.add_parser('library', help='Library mode, syncs library to with an EroGameScape account.')
    library.set_defaults(func=sync_backlog)
    library.add_argument('eroge_root', help='Library directory.', metavar='DIR')
    library.add_argument('dump_root', help='Dumps directory.', metavar='DIR')
    library.add_argument('-u', '--user', action='store', dest='user', help='Username on EroGameScape.')
    library.add_argument('-o', '--offline', action='store_true', dest='offline', help='Use latest existing dump in dump_root.', default=False)
    library.add_argument('-n', '--nodump', action='store_false', dest='dumap', help='Create a file copy of EroGameScape\'s account\'s data in dump_root. (Requires --user)', default=True)

    if len(argv) == 1:
        # parser.print_help()
        print('Running in console mode. Enter "exit" to exit.')
        inp = input('>')
        while inp != 'exit':
            try:
                args = parser.parse_args(shlex.split(inp))
                command_args = vars(args).copy()
                del command_args['func']
                args.func(**command_args)
            except ArgumentError as e:
                parser.print_help()
            inp = input('>')
    else:
        try:
            args = parser.parse_args(argv[1:])
            command_args = vars(args).copy()
            del command_args['func']
            args.func(**command_args)
        except ArgumentError as e:
            parser.print_help()
