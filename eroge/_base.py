# -*- encoding:utf-8 -*-
import os
import shutil

import regex
from copy import deepcopy
from deepdiff import DeepDiff
from deepdiff.helper import CannotCompare
from pathvalidate import is_valid_filepath

from eroge.trackers import *
from eroge.enums import Modes
import eroge.helper as helper


def compare_func(x, y, level=None):
    try:
        return x['id'] == y['id']
    except Exception:
        raise CannotCompare() from None


tokuten = ['壁紙', 'イラスト', 'レーベル', 'ジャケット', 'マニュアル', 'アイコン', 'ヘッダー', 'あざらしWalker']
# quotes
dquotes = [('「', '」'), ('『', '』'), ('“', '”')]
# special edits
del_g = []
del_b = []
del_v = []
del_r = []
sg = {}
sb = {}
sv = {'v3182': 'SHANGRLIA'}
sr = {}


def parse_skip_str(s):
    if regex.match(r'$(\d+\-\d+|\d+)( (\d+\-\d+|\d+))*^', s) is None:
        return None
    else:
        skip = set()
        ls = s.split(' ')
    for i in range(len(ls)):
        if '-' in ls[i]:
            spl = ls[i].split('-')
            skip.add(set(range(int(spl[0]), int(spl[1]) + 1)))
        else:
            skip.add(int(ls[i]))
    return skip


def special_chars_to_full_width(string, dquotes=dquotes[2]):
    # \/:*?"<>|
    # WON'T REPLACE <> AND F NTFS (actually haven't encountered yet（；ﾟдﾟ）ｺﾁｺﾁ)
    if string.endswith('.'):
        # print(f'TRAILING PERIOD（；ﾟдﾟ）ﾋｨｨｨ Title: {string}')
        string = string[:-1]
    lis = []
    flag = False
    for c in string:
        if c == '<' or c == '>':
            print(f'<> IN TITLE（；ﾟдﾟ）ﾋｨｨｨ Title: {string}')
            input()
            raise ValueError
        elif c == '\\':
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


def special_visual_title(t, id):
    st = sv.get(id)
    if st is not None:
        return st
    return t


def special_release_title(t, id):
    st = sv.get(id)
    if st is not None:
        return st
    return t


def infer_pdump(backlog_root):
    print('Inferring previous dump data from folder structure...')
    dmp = ['Inferred']
    walkie = helper.walklevel(backlog_root, depth=1)
    next(walkie)
    for dir, _, files in walkie:
            name = os.path.basename(dir)
            bid = next(filter(lambda x: regex.match(r'^\d+$', x) is not None, files), None)
            if bid is None:
                continue
            dmp.append(dict())
            dmp[-1]['id'] = bid
            dmp[-1]['name'] = name
            dmp[-1]['g'] = []
            talkie = helper.walklevel(os.path.join(backlog_root, name), depth=1)
            next(talkie)
            for dir2, _, files2 in talkie:
                title = os.path.basename(dir2)
                gid = next(filter(lambda x: regex.match(r'^\d+$', x) is not None, files2), None)
                if gid is None:
                    continue
                dmp[-1]['g'].append(dict())
                dmp[-1]['g'][-1]['id'] = gid
                dmp[-1]['g'][-1]['name'] = title

    return dmp


def get_dump(dump_root, tracker=None, user=None, is_none_allowed=False):
    if tracker is None:
        tracker = get_tracker()
    dmp = TRACKERS[tracker].get_dump(dump_root=dump_root, user=user, none=is_none_allowed)
    return dmp


def clean_dump(tracker, dmp_):
    dmp = deepcopy(dmp_)
    if tracker == 'egs':
        i = 1
        while i < len(dmp):
            bid = dmp[i]['bid']
            del dmp[i]['bid']
            dmp[i]['id'] = bid
            title = sb.get(bid)
            if title is None:
                for del_name in del_b:
                    dmp[i]['bname'] = dmp[i]['bname'].replace(del_name, '')
                dmp[i]['name'] = special_chars_to_full_width(dmp[i]['bname'])
            else:
                dmp[i]['name'] = title
            del dmp[i]['bname']
            j = 0
            dmp[i]['g'] = []
            while j < len(dmp[i]['gid']):
                if dmp[i]['possession'][j]:
                    title = sg.get(dmp[i]['gname'][j])
                    if title is None:
                        for del_name in del_g:
                            dmp[i]['gname'][j] = dmp[i]['gname'].replace(del_name, '')
                        dmp[i]['gname'][j] = special_chars_to_full_width(dmp[i]['gname'][j])
                    else:
                        dmp[i]['gname'][j] = title
                    dmp[i]['g'].append({'id': dmp[i]['gid'][j],
                                        'vid': dmp[i]['vid'][j],
                                        'name': dmp[i]['gname'][j],
                                        'model': dmp[i]['model'][j]
                                        })
                    j += 1
                    continue
                elif dmp[i]['possession'][j] is None:
                    print(f'"possession = None" met! - Title: {dmp[i]["gname"][j]}')
                del dmp[i]['gid'][j]
            if len(dmp[i]['gid']) == 0:
                del dmp[i]
            else:
                for agg_col in ['gid', 'vid', 'gname', 'model', 'possession']:
                    del dmp[i][agg_col]
                i += 1
    else:
        raise NotImplementedError
    return dmp


def write_structure(diff_dmp: DeepDiff, mode, backlog_root, skip=None):
    # 'iterable_item_added', 'values_changed', 'iterable_item_removed'
    # root[\d+] / root[\d+]['g'][\d+]
    # ['name'] = change / add, rem
    # ]['g'][ = release / brand

    if skip is None:
        skip = set()

    def pretty(lod, indent=0):
        if len(lod) == 0:
            return 'None'
        return ('\n' + ' ' * indent).join(map(str, lod))

    badds = []
    gadds = []
    try:
        for level in diff_dmp['iterable_item_added']:
            if 'g' in level.path(output_format='list'):
                gadds.append({'brand': level.up.up.t2['name'],
                              'id': level.t2['id'],
                              'name': level.t2['name']})
            else:
                badds.append({'id': level.t2['id'],
                              'name': level.t2['name']})
                for g in level.t2['g']:
                    gadds.append({'brand': level.t2['name'],
                                  'id': g['id'],
                                  'name': g['name']})
    except KeyError:
        pass

    brems = []
    grems = []
    try:
        for level in diff_dmp['iterable_item_removed']:
            if 'g' in level.path(output_format='list'):
                grems.append({'brand': level.up.up.t1['name'],
                              'id': level.t1['id'],
                              'name': level.t1['name']})
            else:
                brems.append({'id': level.t1['id'],
                              'name': level.t1['name']})
    except KeyError:
        pass

    bchgs = []
    gchgs = []
    try:
        for level in diff_dmp['values_changed']:
            if 'g' in level.path(output_format='list'):
                # using new brand name would be problematic in the case the brand name change gets skipped but game does not
                gchgs.append({'brand': level.up.up.up.t1['name'],
                              'id': level.up.t1['id'],
                              'old': level.t1,
                              'new': level.t2})
            else:
                bchgs.append({'id': level.up.t1['id'],
                              'old': level.t1,
                              'new': level.t2})
    except KeyError:
        pass

    double_trouble = False
    index = 0
    count = [[0, 0, 0], [0, 0, 0]]
    changes = [[[], [], []], [[], [], []]]
    skipped = set()
    finished = set()
    special_check = [None, None]
    try:
        if len(brems) != 0:
            print('Brand deletions:')
            for b in brems:
                index += 1
                path = os.path.join(backlog_root, b['name'])
                if index in skip:
                    skipped.add(path)
                    continue
                if mode == Modes.NORMAL:
                    shutil.move(path, os.path.join('.Deleted', path))
                    changes[0][2].append(b)
                    print(f'{index}) Deleted 「 {path} 」')
                elif mode == Modes.DRYRUN:
                    print(f'{index}) Delete 「 {path} 」')
                count[0][2] += 1
                finished.add(path)

        if len(grems) != 0:
            print('Game deletions:')
            for g in grems:
                index += 1
                path = os.path.join(backlog_root, g['brand'], g['name'])
                if index in skip:
                    if index in skip:
                        skipped.add(path)
                        continue
                if mode == Modes.NORMAL:
                    shutil.move(path, os.path.join('.Deleted', path))
                    changes[1][2].append(g)
                    print(f'{index}) Deleted 「 {path} 」')
                elif mode == Modes.DRYRUN:
                    print(f'{index}) Delete 「 {path} 」')
                count[1][2] += 1
                finished.add(path)

        if len(gchgs) != 0:
            tmp = -1
            gchgs_c = gchgs[:]
            print('Game changes:')
            while tmp != len(gchgs_c):
                tmp = len(gchgs_c)
                i = 0
                while i < len(gchgs_c):
                    opath = os.path.join(backlog_root, gchgs_c[i]['brand'], gchgs_c[i]['old'])
                    npath = os.path.join(backlog_root, gchgs_c[i]['brand'], gchgs_c[i]['new'])
                    if npath not in finished and os.path.exists(npath):
                        if npath in skipped:
                            # TODO: CHECK ISSUES ARISING FROM INDEX += 1 HERE (PROBABLY NONE)
                            index += 1
                            del gchgs_c[i]
                            skipped.add(opath)
                        else:
                            i += 1
                        continue
                    index += 1
                    if index in skip:
                        skipped.add(opath)
                        del gchgs_c[i]
                        continue
                    if mode == Modes.NORMAL:
                        shutil.move(opath, npath)
                        changes[1][1].append(gchgs_c[i])
                        print(f'{index}) Changed 「 {opath} 」 to 「 {npath} 」')
                    elif mode == Modes.DRYRUN:
                        print(f'{index}) Change 「 {opath} 」 to 「 {npath} 」')
                    count[1][1] += 1
                    del gchgs_c[i]
                    finished.add(opath)
                if len(gchgs_c) == 0:
                    break
            else:
                print('Something\'s wrong I can feel it...')
                print(gchgs_c)
                raise Exception

        if len(bchgs) != 0:
            tmp = -1
            bchgs_c = bchgs[:]
            print('Brand changes:')
            while tmp != len(bchgs_c):
                tmp = len(bchgs_c)
                i = 0
                while i < len(bchgs_c):
                    opath = os.path.join(backlog_root, bchgs_c[i]['old'])
                    npath = os.path.join(backlog_root, bchgs_c[i]['new'])
                    if npath not in finished and os.path.exists(npath):
                        if npath in skipped:
                            # TODO: CHECK ISSUES ARISING FROM INDEX += 1 HERE (PROBABLY NONE)
                            index += 1
                            del bchgs_c[i]
                            skipped.add(opath)
                        else:
                            i += 1
                        continue
                    index += 1
                    if index in skip:
                        skipped.add(opath)
                        continue
                    if mode == Modes.NORMAL:
                        shutil.move(opath, npath)
                        changes[0][1].append(bchgs_c[i])
                        print(f'{index}) Changed 「 {opath} 」 to 「 {npath} 」')
                    elif mode == Modes.DRYRUN:
                        print(f'{index}) Change 「 {opath} 」 to 「 {npath} 」')
                    count[0][1] += 1
                    del bchgs_c[i]
                    finished.add(opath)
                if len(bchgs_c) == 0:
                    break
            else:
                print('Something\'s wrong I can feel it...')
                print(bchgs_c)
                raise Exception

        if len(badds) != 0:
            special_check[0] = False
            print('Brand additions:')
            for b in badds:
                path = os.path.join(backlog_root, b['name'])
                index += 1
                if index in skip or path in skipped:
                    continue
                if mode == Modes.NORMAL:
                    special_check[1] = b
                    os.mkdir(path)
                    open(os.path.join(path, b['id']), 'w').close()
                    changes[0][0].append(b)
                    print(f'{index}) Created 「 {path} 」')
                elif mode == Modes.DRYRUN:
                    print(f'{index}) Create 「 {path} 」')
                count[0][0] += 1

        if len(gadds) != 0:
            special_check[0] = True
            print('Game additions:')
            for g in gadds:
                path = os.path.join(backlog_root, g['brand'], g['name'])
                index += 1
                if index in skip or path in skipped:
                    continue
                if mode == Modes.NORMAL:
                    special_check[1] = g
                    os.mkdir(path)
                    open(os.path.join(path, g['id']), 'w').close()
                    changes[1][0].append(g)
                    print(f'{index}) Created 「 {path} 」')
                elif mode == Modes.DRYRUN:
                    print(f'{index}) Create 「 {path} 」')
                count[1][0] += 1

    except Exception as e1:
        if mode == Modes.NORMAL:
            print('An occurred during writing changes. Rolling back...')
            print(repr(e1))
        try:
            if special_check[0] is not None:
                path = [None, None]
                if special_check[0]:
                    path[0] = os.path.join(backlog_root, special_check[1]['brand'], special_check[1]['name'])
                    if os.path.exists(path[0]):
                        path[1] = os.path.join(backlog_root, os.path.join(path[0], special_check[1]['id']))
                        if os.path.exists(path[1]):
                            os.remove(path[1])
                        os.rmdir(path[0])
                else:
                    path[0] = os.path.join(backlog_root, special_check[1]['name'])
                    if os.path.exists(path[0]):
                        path[1] = os.path.join(backlog_root, os.path.join(path[0], special_check[1]['id']))
                        if os.path.exists(path[1]):
                            os.remove(path[1])
                        os.rmdir(path[0])
                special_check[0] = None

            if len(changes[1][0]) != 0:
                print('Rolling back game additions...')
                while len(changes[1][0]) != 0:
                    path = os.path.join(backlog_root, changes[1][0][-1]['brand'], changes[1][0][-1]['name'])
                    os.remove(os.path.join(path, changes[1][0][-1]['id']))
                    os.rmdir(path)
                    del changes[1][0][-1]

            if len(changes[0][0]) != 0:
                print('Rolling back brand additions...')
                while len(changes[0][0]) != 0:
                    path = os.path.join(backlog_root, changes[0][0][-1]['name'])
                    os.remove(os.path.join(path, changes[0][0][-1]['id']))
                    os.rmdir(path)
                    del changes[0][0][-1]

            if len(changes[0][1]) != 0:
                print(f'Rolling back brand changes...')
                while len(changes[0][1]) != 0:
                    opath = os.path.join(backlog_root, changes[0][1][-1]['old'])
                    npath = os.path.join(backlog_root, changes[0][1][-1]['new'])
                    shutil.move(npath, opath)
                    del changes[0][1][-1]

            if len(changes[1][1]) != 0:
                print(f'Rolling back game changes...')
                while len(changes[1][1]) != 0:
                    opath = os.path.join(backlog_root, changes[1][1][-1]['brand'], changes[1][1][-1]['old'])
                    npath = os.path.join(backlog_root, changes[1][1][-1]['brand'], changes[1][1][-1]['new'])
                    shutil.move(npath, opath)
                    del changes[1][1][-1]

            if len(changes[1][2]) != 0:
                print('Rolling back game deletions...')
                while len(changes[1][2]) != 0:
                    path = os.path.join(backlog_root, changes[1][2][-1]['brand'], changes[1][2][-1]['name'])
                    shutil.move(os.path.join('.Deleted', path), path)
                    del changes[1][2][-1]

            if len(changes[0][2]) != 0:
                print(f'Rolling back brand deletions...')
                while len(changes[0][2]) != 0:
                    path = os.path.join(backlog_root, changes[0][2][-1]['name'])
                    shutil.move(os.path.join('.Deleted', path), path)
                    del changes[0][2][-1]

        except Exception as e2:
            print('An error occurred during rolling back.（；ﾟдﾟ）ﾔﾍﾞｪ')
            print(repr(e2))
            double_trouble = True
            if special_check[0] is not None:
                if special_check[0]:
                    changes[1][0].append(special_check[1])
                else:
                    changes[0][0].append(special_check[1])

    print()
    print(f'Planned changes:\n'
          f'  Brand: {sum(count[0])}\n'
          f'    Additions: {count[0][0]}\n'
          f'    Changes: {count[0][1]}\n'
          f'    Deletions: {count[0][2]}\n'
          f'  Game: {sum(count[1])}\n'
          f'    Additions: {count[1][0]}\n'
          f'    Changes: {count[1][1]}\n'
          f'    Deletions: {count[1][2]}\n'
          f'  Total: {sum(map(sum, count))}')
    print()
    count_r = [list(map(len, change)) for change in changes]
    print(f'Carried out changes:\n'
          f'  Brand: {sum(count_r[0])}\n'
          f'    Additions: {count_r[0][0]}\n'
          f'    Changes: {count_r[0][1]}\n'
          f'    Deletions: {count_r[0][2]}\n'
          f'  Game: {sum(count_r[1])}\n'
          f'    Additions: {count_r[1][0]}\n'
          f'    Changes: {count_r[1][1]}\n'
          f'    Deletions: {count_r[1][2]}\n'
          f'  Total: {sum(map(sum, count_r))}')
    if double_trouble:
        print()
        print(f'Couldn\'t rollback:\n'
              f'  Brand:\n'
              f'    Additions: {pretty(changes[0][0], indent=15)}\n'
              f'    Changes: {pretty(changes[0][1], indent=13)}\n'
              f'    Deletions: {pretty(changes[0][2], indent=15)}\n'
              f'  Game:\n'
              f'    Additions: {pretty(changes[1][0], indent=15)}\n'
              f'    Changes: {pretty(changes[1][1], indent=13)}\n'
              f'    Deletions: {pretty(changes[1][2], indent=15)}\n')


def diff(pdmp, cdmp):
    return DeepDiff(pdmp, cdmp, exclude_regex_paths=[r"root\[0\]", r"root\[\d+]\['g']\[\d+]\['vid']",
                                                     r"root\[\d+]\['g']\[\d+]\['model']"],
                    iterable_compare_func=compare_func, ignore_order=True, view='tree')


def get_dumps(dump_root, backlog_root, tracker=None, user=None):
    if tracker is None:
        tracker = get_tracker()
    cdmp = get_dump(dump_root, tracker=tracker, user=user)
    pdmp = get_dump(dump_root, tracker=tracker, is_none_allowed=True)
    if pdmp is None:
        pdmp = infer_pdump(backlog_root)

    return pdmp, cdmp


def sync_backlog(pdmp, cdmp, mode, backlog_root, skip=None):
    if cdmp is None or len(cdmp) == 0:
        raise ValueError
    if pdmp is None or len(pdmp) == 0:
        raise ValueError
    ctracker = regex.match(rules.PATTERN_GLOBAL, cdmp[0]).captures(1)[0]
    if pdmp[0] == 'Inferred':
        pdmp_ = pdmp
    else:
        ptracker = regex.match(rules.PATTERN_GLOBAL, pdmp[0]).captures(1)[0]
        if not ptracker == ctracker:
            raise ValueError
        pdmp_ = clean_dump(ptracker, pdmp)
    cdmp_ = clean_dump(ctracker, cdmp)
    if not is_valid_filepath(backlog_root):
        raise ValueError
    write_structure(diff(pdmp_, cdmp_), mode, backlog_root, skip=skip)

