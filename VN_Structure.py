# -*- encoding:utf-8 -*-
import os
import operator
import shutil
from functools import reduce
import natsort
import json

# quotes
dquotes = [('「', '」'), ('『', '』'), ('“', '”')]
# special edits
sv = {'v3182': 'SHANGRLIA'}
sr = {}
# MODES: 1 = exec, 2 = dry run skip
MODE = 2
skip_lines = []
quick_str = ''
# parse quick_str
if quick_str != '':
    ls = quick_str.split(' ')
    for i in range(len(ls)):
        if '-' in ls[i]:
            spl = ls[i].split('-')
            skip_lines.append(range(int(spl[0]), int(spl[1])+1))
        else:
            skip_lines.append(int(ls[i]))


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


def special_game_edit(n, id):
    v = sv.get(id)
    if v:
        return v
    return n


def special_release_edit(n, id):
    v = sv.get(id)
    if v:
        return v
    return n


def create_structure(db):
    i = 0
    while i < len(db):
        if not db[i]['rid'] or not (db[i]['status'] == 'pending' or db[i]['status'] == 'obtained'):
            del db[i]
            continue
        if db[i]['title_v'] != special_game_edit(db[i]['title_v'], db[i]['vid']):
            db[i]['title_v'] = special_game_edit(db[i]['title_v'], db[i]['vid'])
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
        if db[i]['title_r'] != special_game_edit(db[i]['title_r'], db[i]['rid']):
            db[i]['title_r'] = special_game_edit(db[i]['title_r'], db[i]['rid'])
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


def write_structure(db, prev=None):
    #   mk,ln(src,dst) rename src     rename dst
    # ( ([], [], []) , ([], [], []) , ([], [], []) )
    dirs = (([], [], []), ([], [], []), ([], [], []))
    dels = []

    def mk_dir(dir, sym=None):
        to_mk = dir.split(os.sep)
        to_mk = [os.path.join(*(to_mk[:i + 1])) for i in range(len(to_mk))]
        for d in to_mk:
            if not os.path.exists(d):
                os.mkdir(d)
        if sym:
            if not os.path.exists(sym):
                to_mk = sym.split(os.sep)
                to_mk = [os.path.join(*(to_mk[:i + 1])) for i in range(len(to_mk) - 1)]
                for d in to_mk:
                    if not os.path.exists(d):
                        os.mkdir(d)
                os.symlink(os.path.relpath(dir, os.path.dirname(sym)), sym, target_is_directory=True)
    def mv_dir(src, dst, src_sym=None, dst_sym=None):
        if os.path.exists(dst):
            for path, dirs, files in os.walk(src):
                relPath = os.path.relpath(path, src)
                dstPath = os.path.join(dst, relPath)
                if not os.path.exists(dstPath):
                    os.makedirs(dstPath)
                for file in files:
                    dstFile = os.path.join(dstPath, file)
                    srcFile = os.path.join(path, file)
                    shutil.move(srcFile, dstFile)
            for path, dirs, files in os.walk(src, False):
                path, dirs, files = next(os.walk(path))
                if len(files) == 0 and len(dirs) == 0:
                    os.rmdir(path)
        else:
            to_mk = dst.split(os.sep)
            to_mk = [os.path.join(*(to_mk[:i + 1])) for i in range(len(to_mk) - 1)]
            for d in to_mk:
                if not os.path.exists(d):
                    os.mkdir(d)
            shutil.move(src, dst)
        to_rm = src.split(os.sep)
        to_rm = [os.path.join(*(to_rm[:len(to_rm) - i - 1])) for i in range(1, len(to_rm) - 1)]
        for d in to_rm:
            ls = next(os.walk(d))
            if not len(ls[1]) == len(ls[2]) == 0:
                break
            os.rmdir(d)
        if dst_sym:
            if os.path.exists(src_sym):
                os.remove(src_sym)
            if os.path.exists(dst_sym):
                os.remove(dst_sym)
            else:
                to_mk = dst_sym.split(os.sep)
                to_mk = [os.path.join(*(to_mk[:i + 1])) for i in range(len(to_mk) - 1)]
                for d in to_mk:
                    if not os.path.exists(d):
                        os.mkdir(d)
            if not src_sym == dst_sym:
                to_rm = src_sym.split(os.sep)
                to_rm = [os.path.join(*(to_rm[:len(to_rm) - i - 1])) for i in range(1, len(to_rm) - 1)]
                for d in to_rm:
                    ls = next(os.walk(d))
                    if not len(ls[1]) == len(ls[2]) == 0:
                        break
                    os.rmdir(d)
            os.symlink(os.path.relpath(dst, os.path.dirname(dst_sym)), dst_sym, target_is_directory=True)
    def rm_dir(dir):
        if '/' not in dir:
            ls = next(os.walk(dir))
            if ls[1] == 1 and ls[2] == 0:
                mv_dir(dir, f'Deleted/{dir}')
        else:
            mv_dir(dir, f'Deleted/{dir}')

    for d in db:
        if prev:
            ind = [i for i in range(len(prev)) if prev[i]['vid'] == d['vid'] and prev[i]['rid'] == d['rid']]
            if len(ind) == 0:
                d_old = None
            else:
                d_old = prev.pop(ind[0])
        else:
            d_old = None
        if not d_old or (d['patch'] == d_old['patch'] and d['lang'] == d_old['lang'] and
                         d['title_v'] == d_old['title_v'] and d['title_r'] == d_old['title_r'] and
                         d['platform'] == d_old['platform'] and d['multirelease'] == d_old['multirelease']):
            if d['title_v'] not in dirs[0][0]:
                dirs[0][0].append(d['title_v'])
                dirs[0][0].append(f"{d['title_v']}/Extras")
            if d['multirelease']:
                if d['patch']:
                    dirs[0][1].append(f"Shared releases/Patches/{d['lang']}/{d['platform']}/{d['title_r']}")
                    dirs[0][2].append(f"{d['title_v']}/Patches/{d['lang']}/{d['platform']}/{d['title_r']}")
                else:
                    dirs[0][1].append(f"Shared releases/{d['lang']}/{d['platform']}/{d['title_r']}")
                    dirs[0][2].append(f"{d['title_v']}/{d['lang']}/{d['platform']}/{d['title_r']}")
            else:
                if d['patch']:
                    dirs[0][0].append(f"{d['title_v']}/Patches/{d['lang']}/{d['platform']}/{d['title_r']}")
                else:
                    dirs[0][0].append(f"{d['title_v']}/{d['lang']}/{d['platform']}/{d['title_r']}")
        else:
            if d['multirelease'] != d_old['multirelease']:
                print(f"Can't handle edit of {d_old['title_v']}/{d_old['title_r']} to {d['title_v']}/{d['title_r']} with different multirelease flags!")
                continue
            if d['title_v'] not in dirs[2][0]:
                dirs[1][0].append(d_old['title_v'])
                dirs[2][0].append(d['title_v'])
                dirs[1][0].append(f"{d_old['title_v']}/Extras")
                dirs[2][0].append(f"{d['title_v']}/Extras")
            if d['multirelease']:
                if d['patch']:
                    dirs[1][1].append(f"Shared releases/Patches/{d_old['lang']}/{d_old['platform']}/{d_old['title_r']}")
                    dirs[2][1].append(f"Shared releases/Patches/{d['lang']}/{d['platform']}/{d['title_r']}")
                    dirs[1][2].append(f"{d_old['title_v']}/Patches/{d_old['lang']}/{d_old['platform']}/{d_old['title_r']}")
                    dirs[2][2].append(f"{d['title_v']}/Patches/{d['lang']}/{d['platform']}/{d['title_r']}")
                else:
                    dirs[1][1].append(f"Shared releases/{d_old['lang']}/{d_old['platform']}/{d_old['title_r']}")
                    dirs[2][1].append(f"Shared releases/{d['lang']}/{d['platform']}/{d['title_r']}")
                    dirs[1][2].append(f"{d_old['title_v']}/{d_old['lang']}/{d_old['platform']}/{d_old['title_r']}")
                    dirs[2][2].append(f"{d['title_v']}/{d['lang']}/{d['platform']}/{d['title_r']}")
            else:
                if d['patch']:
                    dirs[1][0].append(f"{d_old['title_v']}/Patches/{d_old['lang']}/{d_old['platform']}/{d_old['title_r']}")
                    dirs[2][0].append(f"{d['title_v']}/Patches/{d['lang']}/{d['platform']}/{d['title_r']}")
                else:
                    dirs[1][0].append(f"{d_old['title_v']}/{d_old['lang']}/{d_old['platform']}/{d_old['title_r']}")
                    dirs[2][0].append(f"{d['title_v']}/{d['lang']}/{d['platform']}/{d['title_r']}")
    if prev:
        for d in prev:
            if d['title_v'] not in dels:
                dels.append(d['title_v'])
            if d['multirelease']:
                if d['patch']:
                    dels.append(f"{d['title_v']}/Patches/{d['lang']}/{d['platform']}/{d['title_r']}")
                else:
                    dels.append(f"{d['title_v']}/{d['lang']}/{d['platform']}/{d['title_r']}")
            else:
                if d['patch']:
                    dels.append(f"{d['title_v']}/Patches/{d['lang']}/{d['platform']}/{d['title_r']}")
                else:
                    dels.append(f"{d['title_v']}/{d['lang']}/{d['platform']}/{d['title_r']}")
    dels.reverse()
    dirs[1][0].reverse()
    dirs[1][1].reverse()
    dirs[1][2].reverse()
    dirs[2][0].reverse()
    dirs[2][1].reverse()
    dirs[2][2].reverse()
    count = [0, 0, 0]
    flag = False
    if not os.path.exists('Shared releases'):
        mk_dir('Shared releases')
    if not os.path.exists('Shared extras'):
        mk_dir('Shared extras')
    if MODE == 1:
        for d in dels:
            if os.path.exists(d):
                rm_dir(d)
                count[2] += 1
        for i in range(len(dirs[1][0])):
            if os.path.exists(dirs[1][0][i]):
                if dirs[2][0][i] != dirs[1][0][i]:
                    mv_dir(dirs[1][0][i], dirs[2][0][i])
                    count[1] += 1
            else:
                if not os.path.exists(dirs[2][0][i]):
                    mk_dir(dirs[2][0][i])
                    count[0] += 1
        for i in range(len(dirs[1][1])):
            if os.path.exists(dirs[1][2][i]) and os.path.exists(dirs[1][1][i]):
                if dirs[2][2][i] != dirs[1][2][i] or dirs[2][1][i] != dirs[1][1][i]:
                    mv_dir(dirs[1][1][i], dirs[2][1][i], src_sym=dirs[1][2][i], dst_sym=dirs[2][2][i])
                    count[1] += 1
            else:
                if not os.path.exists(dirs[2][2][i]):
                    mk_dir(dirs[2][1][i], sym=dirs[2][2][i])
                    count[0] += 1
        for d in dirs[0][0]:
            if not os.path.exists(d):
                mk_dir(d)
                count[0] += 1
        for i in range(len(dirs[0][1])):
            if not os.path.exists(dirs[0][2][i]):
                mk_dir(dirs[0][1][i], sym=dirs[0][2][i])
                count[0] += 1
    elif MODE == 2:
        while True:
            counter = [0, 0, 0]
            if flag:
                print('Deleting...')
            else:
                print('DELETIONS:')
            for d in dels:
                if os.path.exists(d):
                    counter[2] += 1
                    if sum(counter) in skip_lines:
                        continue
                    if flag:
                        rm_dir(d)
                        count[2] += 1
                    else:
                        print(f'{sum(counter)})  {d}')
            if flag:
                print('Editing...')
            else:
                print('EDITS:')
            for i in range(len(dirs[1][0])):
                if os.path.exists(dirs[1][0][i]):
                    if dirs[2][0][i] != dirs[1][0][i]:
                        counter[1] += 1
                        if sum(counter) in skip_lines:
                            continue
                        if flag:
                            mv_dir(dirs[1][0][i], dirs[2][0][i])
                            count[1] += 1
                        else:
                            padding = ' ' * (len(str(sum(counter)))+3)
                            print(f'{sum(counter)})  {dirs[1][0][i]}\n{padding} mv {dirs[2][0][i]}')
                else:
                    if not os.path.exists(dirs[2][0][i]):
                        counter[0] += 1
                        if sum(counter) in skip_lines:
                            continue
                        if flag:
                            mk_dir(dirs[2][0][i])
                            count[0] += 1
                        else:
                            print(f'{sum(counter)})  {dirs[2][0][i]}')
            for i in range(len(dirs[1][1])):
                if os.path.exists(dirs[1][2][i]) and os.path.exists(dirs[1][1][i]):
                    if dirs[2][2][i] != dirs[1][2][i] or dirs[2][1][i] != dirs[1][1][i]:
                        counter[1] += 1
                        if sum(counter) in skip_lines:
                            continue
                        if flag:
                            mv_dir(dirs[1][1][i], dirs[2][1][i], src_sym=dirs[1][2][i], dst_sym=dirs[2][2][i])
                            count[1] += 1
                        else:
                            padding = ' ' * (len(str(sum(counter)))+3)
                            print(f'{sum(counter)})  {dirs[1][2][i]}\n{padding}  ln {dirs[1][1][i]}\n{padding} mv {dirs[2][2][i]}\n{padding}  ln {dirs[2][1][i]}')
                else:
                    if not os.path.exists(dirs[2][2][i]):
                        counter[0] += 1
                        if sum(counter) in skip_lines:
                            continue
                        if flag:
                            mk_dir(dirs[2][1][i], sym=dirs[2][2][i])
                            count[0] += 1
                        else:
                            padding = ' ' * (len(str(sum(counter))) + 3)
                            print(f'{sum(counter)})  {dirs[2][2][i]}\n{padding}  ln {dirs[2][1][i]}')
            if flag:
                print('Creating...')
            else:
                print('CREATIONS:')
            for d in dirs[0][0]:
                if not os.path.exists(d):
                    counter[0] += 1
                    if sum(counter) in skip_lines:
                        continue
                    if flag:
                        mk_dir(d)
                        count[0] += 1
                    else:
                        print(f'{sum(counter)})  {d}')
            for i in range(len(dirs[0][1])):
                if not os.path.exists(dirs[0][2][i]):
                    counter[0] += 1
                    if sum(counter) in skip_lines:
                        continue
                    if flag:
                        mk_dir(dirs[0][1][i], sym=dirs[0][2][i])
                        count[0] += 1
                    else:
                        padding = ' ' * (len(str(sum(counter)))+3)
                        print(f'{sum(counter)})  {dirs[0][2][i]}\n{padding}  ln {dirs[0][1][i]}')
            if flag:
                break
            else:
                if input(f'Execute {counter[0]} creations and {counter[1]} edits and {counter[2]} deletions?\n>'):
                    flag = True
                else:
                    break
    print(f'Created {count[0]} and edited {count[1]} and deleted {count[2]}!')


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
    create_structure(dbc)
    print('Please choose the previous dump.\n1)  None')
    for i in range(len(ls)):
        print(f'{i + 2})  {ls[i]}')
    p = int(input('>')) - 2
    if p == -1:
        write_structure(dbc)
    else:
        p = ls[p]
        fp = open(p, 'r')
        dbp = json.load(fp)
        fp.close()
        create_structure(dbp)
        write_structure(dbc, prev=dbp)
input()
