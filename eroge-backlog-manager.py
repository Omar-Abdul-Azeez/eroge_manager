# -*- encoding:utf-8 -*-
import os
import shutil

import regex
from deepdiff import DeepDiff
from deepdiff.helper import CannotCompare

from enums import *

try:
    import EGS_SQL

    EGS_available = True
except ImportError as _:
    EGS_available = False
try:
    import VNDB_API

    VNDB_available = True
except ImportError as _:
    VNDB_available = False
import helper


def compare_func(x, y, level=None):
    try:
        return x['id'] == y['id']
    except Exception:
        raise CannotCompare() from None


# EXTRAS = ['壁紙', 'イラスト', 'レーベル', 'ジャケット', 'マニュアル', 'アイコン', 'ヘッダー', 'あざらしWalker']
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
    if string[-1] == '.':
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


def clean_dump(type, dmp):
    if type == Types.EGS:

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
    elif type == Types.VNDB:
        pass


def merge_dump(egs, vndb):
    pass  # Don't care atm thx for asking
    # i = 0
    # while i < len(dmp):
    #     if dmp[i]['title'] != special_visual_title(dmp[i]['title'], dmp[i]['id']):
    #         dmp[i]['title'] = special_visual_title(dmp[i]['title'], dmp[i]['id'])
    #     else:
    #         if dmp[i]['title'].count('"') % 2 == 1:
    #             print(f"{dmp[i]['title']} contains an odd number of quotes. Skipping novel!")
    #             del dmp[i]
    #             continue
    #         else:
    #             dmp[i]['title'] = special_chars_to_full_width(dmp[i]['title'])
    #     j = 0
    #     while j < len(dmp[i]['releases']):
    #         if dmp[i]['releases'][j]['title'] != special_visual_title(dmp[i]['releases'][j]['title'], dmp[i]['releases'][j]['id']):
    #             dmp[i]['releases'][j]['title'] = special_visual_title(dmp[i]['releases'][j]['title'], dmp[i]['releases'][j]['id'])
    #         else:
    #             c = dmp[i]['releases'][j]['title'].count('"')
    #             if c == 0:
    #                 dmp[i]['releases'][j]['title'] = special_chars_to_full_width(dmp[i]['releases'][j]['title'])
    #             elif c % 2 == 1:
    #                 print(f"{dmp[i]['releases'][j]['title']} contains an odd number of quotes. Skipping release!")
    #                 del dmp[i]['releases'][j]
    #                 continue
    #             else:
    #                 qInfo = [all([q in dmp[i]['title'] for q in quotes]) for quotes in dquotes]
    #                 # two dynamic qInfo.index(True) will remove cost of any(), reduce() and index()
    #                 if any(qInfo):
    #                     if not reduce(operator.xor, qInfo):
    #                         print(f"{dmp[i]['title']} novel contains mixed quotes. Skipping {dmp[i]['releases'][j]['title']} release!")
    #                         del dmp[i]['releases'][j]
    #                         continue
    #                     else:
    #                         dmp[i]['releases'][j]['title'] = special_chars_to_full_width(dmp[i]['releases'][j]['title'], dquotes[qInfo.index(True)])
    #                 else:
    #                     # replacement can't be determined. using default
    #                     # happens when novel didn't have quotes but release does ???
    #                     dmp[i]['releases'][j]['title'] = special_chars_to_full_width(dmp[i]['releases'][j]['title'])
    #         if 'win' in dmp[i]['releases'][j]['platforms']:
    #             dmp[i]['releases'][j]['platform'] = 'win'
    #         else:
    #             if len(dmp[i]['releases'][j]['platforms']) == 1:
    #                 dmp[i]['releases'][j]['platform'] = dmp[i]['releases'][j]['platforms'][0]
    #             else:
    #                 print(dmp[i]['title'])
    #                 print(dmp[i]['releases'][j]['title'])
    #                 for k in range(len(dmp[i]['releases'][j]['platforms'])):
    #                     print(f"{k+1})  {dmp[i]['releases'][j]['platforms'][k]}")
    #                 k = int(input('Please input the number of which platform to use:\n>'))-1
    #                 dmp[i]['releases'][j]['platform'] = dmp[i]['releases'][j]['platforms'][k]
    #         del dmp[i]['releases'][j]['platforms']
    #         j += 1
    #     if not len(dmp[i]['releases']):
    #         del dmp[i]
    #         continue
    #     i += 1


def write_structure(diff_dmp: DeepDiff, mode, root='.', skip=None, cv_path=None):
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
                gadds.append({'brand': level.up.t2['name'],
                              'id': level.t2['id'],
                              'name': level.t2['name']})
            else:
                badds.append({'id': level.t2['id'],
                              'name': level.t2['name']})
                for g in level.t2['g']:
                    gadds.append({'brand': level.t2['name'],
                                  'id': g['id'],
                                  'name': g['name']})
    except KeyError as _:
        pass

    brems = []
    grems = []
    try:
        for level in diff_dmp['iterable_item_removed']:
            if 'g' in level.path(output_format='list'):
                grems.append({'brand': level.up.t1['name'],
                              'id': level.t1['id'],
                              'name': level.t1['name']})
            else:
                brems.append({'id': level.t1['id'],
                              'name': level.t1['name']})
    except KeyError as _:
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
    except KeyError as _:
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
                path = os.path.join(root, b['name'])
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
                path = os.path.join(root, g['brand'], g['name'])
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
                    opath = os.path.join(root, gchgs_c[i]['brand'], gchgs_c[i]['old'])
                    npath = os.path.join(root, gchgs_c[i]['brand'], gchgs_c[i]['new'])
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
                    opath = os.path.join(root, bchgs_c[i]['old'])
                    npath = os.path.join(root, bchgs_c[i]['new'])
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
                path = os.path.join(root, b['name'])
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
                path = os.path.join(root, g['brand'], g['name'])
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

    except:
        try:
            if special_check[0] is not None:
                path = [None, None]
                if special_check[0]:
                    path[0] = os.path.join(root, special_check[1]['brand'], special_check[1]['name'])
                    if os.path.exists(path[0]):
                        path[1] = os.path.join(root, os.path.join(path[0], special_check[1]['id']))
                        if os.path.exists(path[1]):
                            os.remove(path[1])
                        os.rmdir(path[0])
                else:
                    path[0] = os.path.join(root, special_check[1]['name'])
                    if os.path.exists(path[0]):
                        path[1] = os.path.join(root, os.path.join(path[0], special_check[1]['id']))
                        if os.path.exists(path[1]):
                            os.remove(path[1])
                        os.rmdir(path[0])
                special_check[0] = None

            if len(changes[1][0]) != 0:
                print('Rolling back game additions...')
                while len(changes[1][0]) != 0:
                    path = os.path.join(root, changes[1][0][-1]['brand'], changes[1][0][-1]['name'])
                    os.remove(os.path.join(path, changes[1][0][-1]['id']))
                    os.rmdir(path)
                    del changes[1][0][-1]

            if len(changes[0][0]) != 0:
                print('Rolling back brand additions...')
                while len(changes[0][0]) != 0:
                    path = os.path.join(root, changes[0][0][-1]['name'])
                    os.remove(os.path.join(path, changes[0][0][-1]['id']))
                    os.rmdir(path)
                    del changes[0][0][-1]

            if len(changes[0][1]) != 0:
                print(f'Rolling back brand changes...')
                while len(changes[0][1]) != 0:
                    opath = os.path.join(root, changes[0][1][-1]['old'])
                    npath = os.path.join(root, changes[0][1][-1]['new'])
                    shutil.move(npath, opath)
                    del changes[0][1][-1]

            if len(changes[1][1]) != 0:
                print(f'Rolling back game changes...')
                while len(changes[1][1]) != 0:
                    opath = os.path.join(root, changes[1][1][-1]['brand'], changes[1][1][-1]['old'])
                    npath = os.path.join(root, changes[1][1][-1]['brand'], changes[1][1][-1]['new'])
                    shutil.move(npath, opath)
                    del changes[1][1][-1]

            if len(changes[1][2]) != 0:
                print('Rolling back game deletions...')
                while len(changes[1][2]) != 0:
                    path = os.path.join(root, changes[1][2][-1]['brand'], changes[1][2][-1]['name'])
                    shutil.move(os.path.join('.Deleted', path), path)
                    del changes[1][2][-1]

            if len(changes[0][2]) != 0:
                print(f'Rolling back brand deletions...')
                while len(changes[0][2]) != 0:
                    path = os.path.join(root, changes[0][2][-1]['name'])
                    shutil.move(os.path.join('.Deleted', path), path)
                    del changes[0][2][-1]

        except:
            print('An error occured while rolling back changes...（；ﾟдﾟ）ﾔﾍﾞｪ')
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

    # def mk_cover(game, id, cv, url):
    #     path = f'{game}{os.sep}'
    #     if cv_path is None:
    #         cv_img = cfscrape.create_scraper().get(url)
    #         cv_img.decode_content = True
    #         if os.path.exists(f'{path}{id}.jpg'):
    #             os.remove(f'{path}{id}.jpg')
    #         with open(f'{path}{id}.jpg', 'wb') as f:
    #             f.write(cv_img.content)
    #     else:
    #         if os.path.exists(f'{path}{id}.jpg'):
    #             os.remove(f'{path}{id}.jpg')
    #         shutil.copyfile(f'{cv_path}{os.sep}{cv[-2:]}{os.sep}{cv[2:]}.jpg', f'{path}{id}.jpg')
    #     img = Image.open(f'{path}{id}.jpg').convert('RGBA')
    #     wsz = 256
    #     perc = (wsz/float(img.size[1]))
    #     hsz = int((float(img.size[0])*float(perc)))
    #     img = img.resize((hsz, wsz), Image.LANCZOS)
    #     bg = wsz if wsz > hsz else hsz
    #     ico = Image.new('RGBA', (bg,bg), (0, 0, 0, 0))
    #     offset = (round(((bg-hsz) / 2)), round(((bg-wsz) / 2)))
    #     ico.paste(img, offset)
    #     if os.path.exists(f'{path}{id}.ico'):
    #         os.remove(f'{path}{id}.ico')
    #     ico.save(f'{path}{id}.ico')
    #     img.close()
    #     ico.close()
    #     if os.path.exists(f'{path}desktop.ini'):
    #         os.remove(f'{path}desktop.ini')
    #     try:
    #         with open(f'{path}desktop.ini', 'w', encoding='ANSI') as f:
    #             f.write('[.ShellClassInfo]\nConfirmFileOp=0\n')
    #             f.write(f'IconResource={id}.ico,0')
    #             f.write(f'\nIconFile={id}.ico\nIconIndex=0')
    #     except UnicodeEncodeError as e:
    #         with open(f'{path}desktop.ini', 'w', encoding='utf-8') as f:
    #             f.write('[.ShellClassInfo]\nConfirmFileOp=0\n')
    #             f.write(f'IconResource={id}.ico,0')
    #             f.write(f'\nIconFile={id}.ico\nIconIndex=0')
    #     os.system(f'attrib +r "{game}"')
    #     os.system(f'attrib +h "{path}desktop.ini"')
    #     os.system(f'attrib +h "{path}{id}.ico"')
    #     def mk_dir(dir, sym=None):
    #         to_mk = dir.split(os.sep)
    #         to_mk = [os.path.join(*(to_mk[:i + 1])) for i in range(len(to_mk))]
    #         for d in to_mk:
    #             if not os.path.exists(d):
    #                 os.mkdir(d)
    #         if sym:
    #             if not os.path.exists(sym):
    #                 to_mk = sym.split(os.sep)
    #                 to_mk = [os.path.join(*(to_mk[:i + 1])) for i in range(len(to_mk) - 1)]
    #                 for d in to_mk:
    #                     if not os.path.exists(d):
    #                         os.mkdir(d)
    #                 os.symlink(os.path.relpath(dir, os.path.dirname(sym)), sym, target_is_directory=True)
    # def mv_dir(src, dst, src_sym=None, dst_sym=None):
    #     if os.path.exists(dst):
    #         for path, dirs, files in os.walk(src):
    #             relPath = os.path.relpath(path, src)
    #             dstPath = os.path.join(dst, relPath)
    #             if not os.path.exists(dstPath):
    #                 os.makedirs(dstPath)
    #             for file in files:
    #                 dstFile = os.path.join(dstPath, file)
    #                 srcFile = os.path.join(path, file)
    #                 shutil.move(srcFile, dstFile)
    #         for path, dirs, files in os.walk(src, False):
    #             path, dirs, files = next(os.walk(path))
    #             if len(files) == 0 and len(dirs) == 0:
    #                 os.rmdir(path)
    #     else:
    #         to_mk = dst.split(os.sep)
    #         to_mk = [os.path.join(*(to_mk[:i + 1])) for i in range(len(to_mk) - 1)]
    #         for d in to_mk:
    #             if not os.path.exists(d):
    #                 os.mkdir(d)
    #         shutil.move(src, dst)
    #     to_rm = src.split(os.sep)
    #     to_rm = [os.path.join(*(to_rm[:len(to_rm) - i - 1])) for i in range(1, len(to_rm) - 1)]
    #     for d in to_rm:
    #         ls = next(os.walk(d))
    #         if not len(ls[1]) == len(ls[2]) == 0:
    #             break
    #         os.rmdir(d)
    #     if dst_sym:
    #         if os.path.exists(src_sym):
    #             os.remove(src_sym)
    #         if os.path.exists(dst_sym):
    #             os.remove(dst_sym)
    #         else:
    #             to_mk = dst_sym.split(os.sep)
    #             to_mk = [os.path.join(*(to_mk[:i + 1])) for i in range(len(to_mk) - 1)]
    #             for d in to_mk:
    #                 if not os.path.exists(d):
    #                     os.mkdir(d)
    #         if not src_sym == dst_sym:
    #             to_rm = src_sym.split(os.sep)
    #             to_rm = [os.path.join(*(to_rm[:len(to_rm) - i - 1])) for i in range(1, len(to_rm) - 1)]
    #             for d in to_rm:
    #                 ls = next(os.walk(d))
    #                 if not len(ls[1]) == len(ls[2]) == 0:
    #                     break
    #                 os.rmdir(d)
    #         os.symlink(os.path.relpath(dst, os.path.dirname(dst_sym)), dst_sym, target_is_directory=True)
    # def rm_dir(dir):
    #     if os.sep not in dir:
    #         ls = next(os.walk(dir))
    #         if len(set(ls[1]) - {'Extras'}) == 0 and len(set(ls[2]) - {'desktop.ico', f'{dir}.ico', f'{dir}.jpg'}) == 0:
    #             mv_dir(dir, f'Deleted{os.sep}{dir}')
    #     else:
    #         mv_dir(dir, f'Deleted{os.sep}{dir}')
    #
    # for v in db:
    #     if prev_db:
    #         ind = [i for i in range(len(prev_db)) if prev_db[i]['id'] == v['id']]
    #         if len(ind) == 0:
    #             v_old = None
    #         else:
    #             v_old = prev_db.pop(ind[0])
    #     else:
    #         v_old = None
    #     if not v_old:
    #         dirs[0][0].append(v['title'])
    #         dirs[0][0].append(os.sep.join(('Extras', v['title'])))
    #         dirs[3].append([v['title'], v['id'], *v['cover']])
    #         for r in v['releases']:
    #             if len(r['vns']) > 1:
    #                 if r['patch']:
    #                     dirs[0][1].append(os.sep.join(('Shared releases', 'Patches', r['platform'], r['title'])))
    #                     dirs[0][2].append(os.sep.join((v['title'], 'Patches', r['platform'], r['title'])))
    #                 else:
    #                     dirs[0][1].append(os.sep.join(('Shared releases', r['platform'], r['title'])))
    #                     dirs[0][2].append(os.sep.join((v['title'], r['platform'], r['title'])))
    #             else:
    #                 if v['patch']:
    #                     dirs[0][0].append(os.sep.join((v['title'], 'Patches', r['platform'], r['title'])))
    #                 else:
    #                     dirs[0][0].append(os.sep.join((v['title'], r['platform'], r['title'])))
    #     elif v['title'] == v_old['title']:
    #         pass
    #     else:
    #         if v['multirelease'] != v_old['multirelease']:
    #             print(f"Can't handle edit of {v_old['title_v']}/{v_old['title_r']} to {v['title_v']}/{v['title_r']} with different multirelease flags!")
    #             continue
    #         if v['title_v'] not in dirs[2][0]:
    #             dirs[1][0].append(v_old['title_v'])
    #             dirs[2][0].append(v['title_v'])
    #             if icons and (v['cv'] != v_old['cv'] or v['title_v'] != v_old['title_v']):
    #                 dirs[3].append((v['title_v'], v['cv']))
    #             dirs[1][0].append(os.sep.join((v_old['title_v'], 'Extras')))
    #             dirs[2][0].append(os.sep.join((v['title_v'], 'Extras')))
    #         if v['multirelease']:
    #             if v['patch']:
    #                 dirs[1][1].append(os.sep.join(('Shared releases', 'Patches', v_old['lang'], v_old['platform'], v_old['title_r'])))
    #                 dirs[2][1].append(os.sep.join(('Shared releases', 'Patches', v['lang'], v['platform'], v['title_r'])))
    #                 dirs[1][2].append(os.sep.join((v_old['title_v'], 'Patches', v_old['lang'], v_old['platform'], v_old['title_r'])))
    #                 dirs[2][2].append(os.sep.join((v['title_v'], 'Patches', v['lang'], v['platform'], v['title_r'])))
    #             else:
    #                 dirs[1][1].append(os.sep.join(('Shared releases', v_old['lang'], v_old['platform'], v_old['title_r'])))
    #                 dirs[2][1].append(os.sep.join(('Shared releases', v['lang'], v['platform'], v['title_r'])))
    #                 dirs[1][2].append(os.sep.join((v_old['title_v'], v_old['lang'], v_old['platform'], v_old['title_r'])))
    #                 dirs[2][2].append(os.sep.join((v['title_v'], v['lang'], v['platform'], v['title_r'])))
    #         else:
    #             if v['patch']:
    #                 dirs[1][0].append(os.sep.join((v_old['title_v'], 'Patches', v_old['lang'], v_old['platform'], v_old['title_r'])))
    #                 dirs[2][0].append(os.sep.join((v['title_v'], 'Patches', v['lang'], v['platform'], v['title_r'])))
    #             else:
    #                 dirs[1][0].append(os.sep.join((v_old['title_v'], v_old['lang'], v_old['platform'], v_old['title_r'])))
    #                 dirs[2][0].append(os.sep.join((v['title_v'], v['lang'], v['platform'], v['title_r'])))
    # if prev_db:
    #     for v_old in prev_db:
    #         if v_old['title_v'] not in dels:
    #             dels.append(v_old['title_v'])
    #         if v_old['multirelease']:
    #             if v_old['patch']:
    #                 dels.append(os.sep.join((v_old['title_v'], 'Patches', v_old['lang'], v_old['platform'], v_old['title_r'])))
    #             else:
    #                 dels.append(os.sep.join((v_old['title_v'], v_old['lang'], v_old['platform'], v_old['title_r'])))
    #         else:
    #             if v_old['patch']:
    #                 dels.append(os.sep.join((v_old['title_v'], 'Patches', v_old['lang'], v_old['platform'], v_old['title_r'])))
    #             else:
    #                 dels.append(os.sep.join((v_old['title_v'], v_old['lang'], v_old['platform'], v_old['title_r'])))
    # dels.reverse()
    # dirs[1][0].reverse()
    # dirs[1][1].reverse()
    # dirs[1][2].reverse()
    # dirs[2][0].reverse()
    # dirs[2][1].reverse()
    # dirs[2][2].reverse()
    # count = [0, 0, 0]
    # flag = False
    # if not os.path.exists('Shared releases'):
    #     mk_dir('Shared releases')
    # if not os.path.exists(os.sep.join(('Extras', 'Shared extras'))):
    #     mk_dir(os.sep.join(('Extras', 'Shared extras')))
    # if MODE == 1:
    #     for v in dels:
    #         if os.path.exists(v):
    #             rm_dir(v)
    #             count[2] += 1
    #     for i in range(len(dirs[1][0])):
    #         if os.path.exists(dirs[1][0][i]):
    #             if dirs[2][0][i] != dirs[1][0][i]:
    #                 mv_dir(dirs[1][0][i], dirs[2][0][i])
    #                 count[1] += 1
    #         else:
    #             if not os.path.exists(dirs[2][0][i]):
    #                 mk_dir(dirs[2][0][i])
    #                 count[0] += 1
    #     for i in range(len(dirs[1][1])):
    #         if os.path.exists(dirs[1][2][i]) and os.path.exists(dirs[1][1][i]):
    #             if dirs[2][2][i] != dirs[1][2][i] or dirs[2][1][i] != dirs[1][1][i]:
    #                 mv_dir(dirs[1][1][i], dirs[2][1][i], src_sym=dirs[1][2][i], dst_sym=dirs[2][2][i])
    #                 count[1] += 1
    #                 multirelease_edits[0].append(dirs[1][1][i])
    #                 multirelease_edits[1].append(dirs[2][1][i])
    #         else:
    #             if not os.path.exists(dirs[2][2][i]):
    #                 mk_dir(dirs[2][1][i], sym=dirs[2][2][i])
    #                 count[0] += 1
    #     for v in dirs[0][0]:
    #         if not os.path.exists(v):
    #             mk_dir(v)
    #             count[0] += 1
    #     for i in range(len(dirs[0][1])):
    #         if not os.path.exists(dirs[0][2][i]):
    #             mk_dir(dirs[0][1][i], sym=dirs[0][2][i])
    #             count[0] += 1
    #     for v in dirs[3]:
    #         mk_cover(*v)
    # elif MODE == 2:
    #     while True:
    #         counter = [0, 0, 0]
    #         if flag:
    #             print('Deleting...')
    #         else:
    #             print('DELETIONS:')
    #         for v in dels:
    #             if os.path.exists(v):
    #                 counter[2] += 1
    #                 if sum(counter) in skip_lines:
    #                     continue
    #                 if flag:
    #                     rm_dir(v)
    #                     count[2] += 1
    #                 else:
    #                     print(f'{sum(counter)})  {v}')
    #         if flag:
    #             print('Editing...')
    #         else:
    #             print('EDITS:')
    #         for i in range(len(dirs[1][0])):
    #             if os.path.exists(dirs[1][0][i]):
    #                 if dirs[2][0][i] != dirs[1][0][i]:
    #                     counter[1] += 1
    #                     if sum(counter) in skip_lines:
    #                         continue
    #                     if flag:
    #                         mv_dir(dirs[1][0][i], dirs[2][0][i])
    #                         count[1] += 1
    #                     else:
    #                         padding = ' ' * (len(str(sum(counter)))+3)
    #                         print(f'{sum(counter)})  {dirs[1][0][i]}\n{padding} mv {dirs[2][0][i]}')
    #             else:
    #                 if not os.path.exists(dirs[2][0][i]):
    #                     counter[0] += 1
    #                     if sum(counter) in skip_lines:
    #                         continue
    #                     if flag:
    #                         mk_dir(dirs[2][0][i])
    #                         count[0] += 1
    #                     else:
    #                         print(f'{sum(counter)})  {dirs[2][0][i]}')
    #         for i in range(len(dirs[1][1])):
    #             if os.path.exists(dirs[1][2][i]) and os.path.exists(dirs[1][1][i]):
    #                 if dirs[2][2][i] != dirs[1][2][i] or dirs[2][1][i] != dirs[1][1][i]:
    #                     counter[1] += 1
    #                     if sum(counter) in skip_lines:
    #                         continue
    #                     if flag:
    #                         mv_dir(dirs[1][1][i], dirs[2][1][i], src_sym=dirs[1][2][i], dst_sym=dirs[2][2][i])
    #                         count[1] += 1
    #                         multirelease_edits[0].append(dirs[1][1][i])
    #                         multirelease_edits[1].append(dirs[2][1][i])
    #                     else:
    #                         padding = ' ' * (len(str(sum(counter)))+3)
    #                         print(f'{sum(counter)})  {dirs[1][2][i]}\n{padding}  ln {dirs[1][1][i]}\n{padding} mv {dirs[2][2][i]}\n{padding}  ln {dirs[2][1][i]}')
    #             else:
    #                 if not os.path.exists(dirs[2][2][i]):
    #                     counter[0] += 1
    #                     if sum(counter) in skip_lines:
    #                         continue
    #                     if flag:
    #                         mk_dir(dirs[2][1][i], sym=dirs[2][2][i])
    #                         count[0] += 1
    #                     else:
    #                         padding = ' ' * (len(str(sum(counter))) + 3)
    #                         print(f'{sum(counter)})  {dirs[2][2][i]}\n{padding}  ln {dirs[2][1][i]}')
    #         if flag:
    #             print('Creating...')
    #         else:
    #             print('CREATIONS:')
    #         for g in dirs[0][0]:
    #             if not os.path.exists(g):
    #                 counter[0] += 1
    #                 if sum(counter) in skip_lines:
    #                     continue
    #                 if flag:
    #                     mk_dir(g)
    #                     count[0] += 1
    #                 else:
    #                     print(f'{sum(counter)})  {g}')
    #         for i in range(len(dirs[0][1])):
    #             if not os.path.exists(dirs[0][2][i]):
    #                 counter[0] += 1
    #                 if sum(counter) in skip_lines:
    #                     continue
    #                 if flag:
    #                     mk_dir(dirs[0][1][i], sym=dirs[0][2][i])
    #                     count[0] += 1
    #                 else:
    #                     padding = ' ' * (len(str(sum(counter)))+3)
    #                     print(f'{sum(counter)})  {dirs[0][2][i]}\n{padding}  ln {dirs[0][1][i]}')
    #         if flag and icons:
    #             for c in dirs[3]:
    #                 mk_cover(*c)
    #         if not flag:
    #             nl = '\n'
    #             if input(f'Execute {counter[0]} creations and {counter[1]} edits and {counter[2]} deletions?\nMultirelease edits:\n{nl.join([" -> ".join(x) for x in zip(multirelease_edits[0], multirelease_edits[1])])}\n>'):
    #                 flag = True
    #         else:
    #             break
    # nl = '\n'
    # print(f'Created {count[0]} and edited {count[1]} and deleted {count[2]}!\nPlease check these for any dead links:\n{nl.join([" -> ".join(x) for x in zip(multirelease_edits[0], multirelease_edits[1])])}')


def infer_dump(type, root='.'):
    print('Inferring previous dump data from folder structure...')
    if type == Types.EGS:
        dmp = ['EGS-ubg-Inferred']
        walkie = helper.walklevel(root, depth=1)
        next(walkie)
        for dir, _, files in walkie:
            name = dir[2:]
            bid = next(filter(lambda x: regex.match(r'$\d+^', x) is not None, files), None)
            if bid is None:
                continue
            dmp.append(dict())
            dmp[-1]['id'] = bid
            dmp[-1]['name'] = name
            dmp[-1]['g'] = []
            talkie = helper.walklevel(os.sep.join([root, name]), depth=1)
            next(talkie)
            for dir2, _, files2 in talkie:
                title = dir2.rsplit(os.sep, maxsplit=1)[1]
                gid = next(filter(lambda x: regex.match(r'$\d+^', x) is not None, files2), None)
                if gid is None:
                    continue
                dmp[-1]['g'].append(dict())
                dmp[-1]['g'][-1]['id'] = gid
                dmp[-1]['g'][-1]['name'] = title
    elif type == Types.VNDB:
        dmp = ['VNDB-Inferred']
    elif type == Types.EGS_VNDB:
        dmp = ['EGS-VNDB-Inferred']

    return dmp


def read_dump(type, root='.', can_dl=False, user=None, none=False):
    if type == Types.EGS:
        dmp = EGS_SQL.get_dump('ubg', root=root, can_dl=can_dl, user=user, none=none)
        if dmp is None:
            return None
        if can_dl:
            ls = EGS_SQL.local_dumps('ubg', root=root)
            if dmp[0] + '.json' not in ls:
                EGS_SQL.write_dump(dmp=dmp, root=root)
    elif type == Types.VNDB:
        dmp = VNDB_API.get_dump(False, root=root, can_dl=can_dl, user=user, none=none)
        if dmp is None:
            return None
        if can_dl:
            ls = VNDB_API.local_dumps(False, root=root)
            if dmp[0] + '.json' not in ls:
                VNDB_API.write_dump(dmp=dmp, root=root)

    return dmp


def choose_dumps(type, root='.', user=None):
    if (type == Types.EGS and EGS_available and not bool(input('Use EGS? empty for Y anything for N\n>'))) or (
            type == Types.VNDB and VNDB_available and bool(input('Use VNDB? empty for N anything for Y\n>'))):
        cdmp = read_dump(type, root=root, can_dl=True, user=user)
        pdmp = read_dump(type, root=root, none=True)
        if pdmp is None:
            pdmp = infer_dump(type, root=root)
        clean_dump(type, cdmp)
        clean_dump(type, pdmp)
    else:
        cdmp = None
        pdmp = None

    return pdmp, cdmp


def diff(pdmp, cdmp):
    return DeepDiff(pdmp, cdmp, exclude_regex_paths=[r"root\[0\]", r"root\[\d+]\['g']\[\d+]\['vid']",
                                                     r"root\[\d+]\['g']\[\d+]\['model']"],
                    iterable_compare_func=compare_func, ignore_order=True, view='tree')


def main():
    skip_str = ''
    skip = parse_skip_str(skip_str)

    if EGS_available and not bool(input('Use EGS? empty for Y anything for N\n>')):
        cdmp_egs = read_dump(Types.EGS, can_dl=True)
        pdmp_egs = read_dump(Types.EGS, none=True)
        if pdmp_egs is None:
            pdmp_egs = infer_dump(Types.EGS)
        clean_dump(Types.EGS, cdmp_egs)
        clean_dump(Types.EGS, pdmp_egs)
    else:
        cdmp_egs = None
        pdmp_egs = None

    cv_path = None
    if VNDB_available and bool(input('Use VNDB? empty for N anything for Y\n>')):
        cdmp_vndb = read_dump(Types.VNDB, can_dl=True)
        pdmp_vndb = read_dump(Types.VNDB, none=True)
        if pdmp_vndb is None:
            pdmp_vndb = infer_dump(Types.VNDB)
        clean_dump(Types.VNDB, cdmp_vndb)
        clean_dump(Types.VNDB, pdmp_vndb)
        if not bool(input('Create icons for folders? empty for Y anything for N\n>')):
            cv_path = input('VNDB covers dump path: leave empty to download covers\n>')
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
            pdmp_egs = infer_dump(Types.EGS_VNDB)
    elif cdmp_egs is not None:
        cdmp_egs = cdmp_egs
        if pdmp_egs is not None:
            pdmp_egs = pdmp_egs
        else:
            pdmp_egs = infer_dump(Types.EGS)
    elif cdmp_vndb is not None:
        cdmp_egs = cdmp_vndb
        if pdmp_vndb is not None:
            pdmp_egs = pdmp_vndb
        else:
            pdmp_egs = infer_dump(Types.VNDB)
    else:
        print('Requires either EGS or VNDB. Please provide.')
        input()
        return

    diff_dmp = diff(pdmp_egs, cdmp_egs)
    write_structure(diff_dmp, Modes.DRYRUN, skip=skip, cv_path=cv_path)
    input()
    write_structure(diff_dmp, Modes.NORMAL, skip=skip, cv_path=cv_path)
    input()


if __name__ == '__main__':
    main()
