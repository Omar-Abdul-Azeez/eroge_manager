# -*- encoding:utf-8 -*-
import os
import operator
from functools import reduce
from bs4 import BeautifulSoup
import itertools
import requests
import natsort
import json

# quotes
dquotes = [['「', '」'], ['『', '』'], ['“', '”']]
# special edits
sv = {'v3182': 'SHANGRLIA'}
sr = {}
# MODES: 0 = mkdir, 1 = dry run skip , 2 = skip
skip_lines = []
MODE = 1

def replace_stuff_with_CJK(string, dquotes=dquotes[0]):
    # \/:*?"<>|
    # WON'T REPLACE <> NOR TRAILING PERIODS AND F NTFS (actually haven't encountered yet)
    if len(string) == 0:
        return string
    lis = []
    flag = False
    for c in string:
        if c == '\\':
            lis.append('＼')
        elif c == '/':
            lis.append('／')
        elif c == ':':
            lis.append('：')
        elif c == '?':
            lis.append('？')
        elif c == '*':
            lis.append('＊')
        elif c == '|':
            lis.append('｜')
        elif c == '"':
            lis.append(dquotes[0] if (flag := not flag) else dquotes[1])
        else:
            lis.append(c)
    return ''.join(lis)


def special_novel_edit(n, id):
    v = sv.get(id)
    if v:
        return v
    return n


def special_release_edit(n, id):
    v = sv.get(id)
    if v:
        return v
    return n


def safe(db):
    i = 0
    while i < len(db):
        if not db[i]['rid'] or not (db[i]['status'] == 'pending' or db[i]['status'] == 'obtained'):
            del db[i]
            continue
        if db[i]['title_v'] != special_novel_edit(db[i]['title_v'], db[i]['vid']):
            db[i]['title_v'] = special_novel_edit(db[i]['title_v'], db[i]['vid'])
        else:
            if db[i]['title_v'].count('"') % 2 == 1:
                print(f"{db[i]['title_v']} contains an odd number of quotes. Skipping novel!")
                continue
            else:
                db[i]['title_v'] = replace_stuff_with_CJK(db[i]['title_v'])
        for j in range(i):
            if db[j]['title_v'] == db[i]['title_v'] and db[j]['vid'] != db[i]['vid']:
                print(f"{db[i]['title_v']} Already exists. Appending visual novel ID!")
                db[i]['title_v'] = f"{db[i]['title_v']} - {db[i]['vid']}"
        if db[i]['title_r'] != special_novel_edit(db[i]['title_r'], db[i]['rid']):
            db[i]['title_r'] = special_novel_edit(db[i]['title_r'], db[i]['rid'])
        else:
            c = db[i]['title_r'].count('"')
            if c == 0:
                db[i]['title_r'] = replace_stuff_with_CJK(db[i]['title_r'])
            elif c % 2 == 1:
                print(f"{db[i]['title_v']} contains an odd number of quotes. Skipping release!")
                continue
            else:
                qInfo = [False not in [q in db[i]['title_v'] for q in quotes] for quotes in dquotes]
                # two dynamic qInfo.index(True) will remove cost of any(), reduce() and index()
                if any(qInfo):
                    if not reduce(operator.xor, qInfo):
                        print(f"{db[i]['title_v']} novel contains mixed quotes. Skipping {db[i]['title_r']} release!")
                        continue
                    else:
                        db[i]['title_r'] = replace_stuff_with_CJK(db[i]['title_r'], dquotes[qInfo.index(True)])
                else:
                    # replacement can't be determined. using default
                    # happens when novel didn't have quotes but release does ???
                    db[i]['title_r'] = replace_stuff_with_CJK(db[i]['title_r'])
        if 'win' in db[i]['platform']:
            db[i]['platform'] = 'win'
        else:
            if len(db[i]['platform']) == 1:
                db[i]['platform'] = db[i]['platform'][0]
            else:
                print(db[i]['title_v'])
                print(db[i]['title_r'])
                for j in range(len(db[i]['platform'])):
                    print(f"{j+1})  {db[i]['platform'][j]}")
                j = int(input('Please input the number of which platform to use:\n>'))-1
                db[i]['platform'] = db[i]['platform'][j]
        if 'en' in db[i]['lang'] and 'ja' not in db[i]['lang']:
            db[i]['lang'] = 'EN'
        elif 'en' not in db[i]['lang'] and 'ja' in db[i]['lang']:
            db[i]['lang'] = 'JP'
        else:
            db[i]['lang'] = 'JP／EN'
        for j in range(i):
            if db[j]['patch'] == db[i]['patch'] and db[j]['platform'] == db[i]['platform'] and db[j]['lang'] == db[i]['lang'] and db[j]['title_r'] == db[i]['title_r'] and db[j]['rid'] != db[i]['rid']:
                print(f"{db[i]['title_r']} Already exists. Appending release ID!")
                db[i]['title_r'] = f"{db[i]['title_r']} - {db[i]['rid']}"
        i += 1


counter = 0
real_counter = [0, 0]
dirs = [[], [], []]


def make_dir(string, mode, sym=None):
    global counter
    global real_counter
    global dirs
    if mode == 0:
        if not os.path.exists(string):
            to_mk = string.split(os.sep)
            to_mk = [os.path.join(*(to_mk[:i+1])) for i in range(len(to_mk))]
            for d in to_mk:
                if not os.path.exists(d):
                    os.mkdir(d)
            real_counter[0] += 1
        if sym:
            if not os.path.exists(sym):
                to_mk = sym.split(os.sep)
                to_mk = [os.path.join(*(to_mk[:i+1])) for i in range(len(to_mk)-1)]
                for d in to_mk:
                    if not os.path.exists(d):
                        os.mkdir(d)
                os.symlink(os.path.relpath(string, os.path.dirname(sym)), sym, target_is_directory=True)
                real_counter[1] += 1
            else:
                pass
    elif mode == 1:
        if not os.path.exists(string) or (sym and not os.path.exists(sym)):
            counter += 1
            if counter not in skip_lines:
                if sym:
                    print(f'{str(counter)})  {sym} -> {string}')
                else:
                    print(f'{str(counter)})  {string}')
    elif mode == 2:
        if not os.path.exists(string) or (sym and not os.path.exists(sym)):
            counter += 1
            if counter not in skip_lines:
                to_mk = string.split(os.sep)
                to_mk = [os.path.join(*(to_mk[:i + 1])) for i in range(len(to_mk))]
                dirs[0].extend(to_mk)
                real_counter[0] += 1
                if sym:
                    if not os.path.exists(sym):
                        to_mk = sym.split(os.sep)
                        to_mk = [os.path.join(*(to_mk[:i + 1])) for i in range(len(to_mk) - 1)]
                        dirs[0].extend(to_mk)
                        dirs[1].append(string)
                        dirs[2].append(sym)
                        real_counter[1] += 1
                    else:
                        pass


def create_structure(db, prev=None):
    global real_counter
    make_dir('Shared releases', MODE)
    make_dir('Shared extras', MODE)
    for d in db:
        make_dir(d['title_v'], MODE)
        make_dir(f"{d['title_v']}/Extras", MODE)
        make_dir(f"{d['title_v']}/Patches", MODE)
        if d['multirelease']:
            if d['patch']:
                make_dir(f"Shared releases/Patches/{d['lang']}/{d['platform']}/{d['title_r']}", MODE,
                         f"{d['title_v']}/Patches/{d['lang']}/{d['platform']}/{d['title_r']}")
            else:
                make_dir(f"Shared releases/{d['lang']}/{d['platform']}/{d['title_r']}", MODE,
                         f"{d['title_v']}/{d['lang']}/{d['platform']}/{d['title_r']}")
        else:
            if d['patch']:
                make_dir(f"{d['title_v']}/Patches/{d['lang']}/{d['platform']}/{d['title_r']}", MODE)
            else:
                make_dir(f"{d['title_v']}/{d['lang']}/{d['platform']}/{d['title_r']}", MODE)

    if MODE == 2 and input(f'Create {real_counter[0]} games and releases and {real_counter[1]} multireleases?\n>'):
        for d in dirs[0]:
            if not os.path.exists(d):
                os.mkdir(d)
        for i in range(len(dirs[1])):
            if not os.path.exists(dirs[1][i]):
                os.mkdir(dirs[1][i])
            if not os.path.exists(dirs[2][i]):
                os.symlink(os.path.relpath(dirs[1][i], os.path.dirname(dirs[2][i])), dirs[2][i], target_is_directory=True)
    print(f'Created {real_counter[0]} games and releases and {real_counter[1]} multireleases!')


ls = natsort.natsorted(filter(lambda x: 'my superior ulist' in x and 'json' in x, next(os.walk('.'))[2]))
if len(ls) == 0:
    input('Please provide a query dump.\n')
    exit()
else:
    print('Please choose the current dump.')
    for i in range(len(ls)):
        print(f'{i+1})  {ls[i]}')
    c = ls[int(input('>'))-1]
    fc = open(c, 'r')
    dbc = json.load(fc)
    fc.close()
    safe(dbc)
    print('Please choose the previous dump.\n1)  None')
    for i in range(len(ls)):
        print(f'{i + 2})  {ls[i]}')
    p = int(input('>')) - 2
    if p == 1:
        create_structure(dbc)
    else:
        p = ls[p]
        fp = open(p, 'r')
        dbp = json.load(fp)
        fp.close()
        safe(dbp)
        create_structure(dbc, prev=dbp)
input()
