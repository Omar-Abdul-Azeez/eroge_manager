# -*- encoding:utf-8 -*-
import os
import shutil
from enum import Enum
from json import load

from deepdiff import DeepDiff

try:
    import EGS_SQL
    EGS_available = True
except ImportError as e:
    EGS_available = False
try:
    import VNDB_API
    VNDB_available = True
except ImportError as e:
    VNDB_available = False
from walklevel import walklevel


class dumps(Enum):
    EGS = 'egs'
    VNDB = 'vndb'
    EGS_VNDB = 'egs + vndb'


class modes(Enum):
    NORMAL = 'normal'
    DRYRUN = 'dryrun'


def ask(msg, choices: list = None, no_choice: bool = False):
    print(msg)
    if choices is not None:
        if no_choice:
            print('1)  None')
        for i in range(len(choices)):
            print(f'{i + (2 if no_choice else 1)})  {choices[i]}')
        return int(input('>')) - (2 if no_choice else 1)
    return input('>')


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
skip = set()
skip_str = ''
# parse skip_str
if skip_str != '':
    ls = skip_str.split(' ')
    for i in range(len(ls)):
        if '-' in ls[i]:
            spl = ls[i].split('-')
            skip.add(set(range(int(spl[0]), int(spl[1]) + 1)))
        else:
            skip.add(int(ls[i]))


def special_chars_to_full_width(string, dquotes=dquotes[2]):
    # \/:*?"<>|
    # WON'T REPLACE <> NOR TRAILING PERIODS AND F NTFS (actually haven't encountered yet（；ﾟдﾟ）ｺﾁｺﾁ)
    if string[-1] == '.':
        print(f'TRAILING PERIOD（；ﾟдﾟ）ﾋｨｨｨ Title: {string}')
        input()
        raise ValueError
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


def clean_egs(dmp):
    to_del = []
    for bid, info in dmp.items():
        title = sb.get(bid)
        if title is None:
            for del_name in del_b:
                info['bname'] = info['bname'].replace(del_name, '')
            info['name'] = special_chars_to_full_width(info['bname'])
        else:
            info['name'] = title
        del info['bname']
        i = 0
        info['g'] = dict()
        while i < len(info['gid']):
            if info['possession'][i]:
                title = sg.get(info['gname'][i])
                if title is None:
                    for del_name in del_g:
                        info['gname'][i] = info['gname'].replace(del_name, '')
                    info['gname'][i] = special_chars_to_full_width(info['gname'][i])
                else:
                    info['gname'][i] = title
                info['g'][info['gid'][i]] = {'vid': info['vid'][i],
                                             'name': info['gname'][i],
                                             'model': info['model'][i]
                                             }
                i += 1
                continue
            elif info['possession'][i] is None:
                print(f'"possession = None" met! - Title: {info["gname"][i]}')
            del info['gid'][i]
        if len(info['gid']) == 0:
            to_del.append(bid)
        else:
            for agg_col in ['gid', 'vid', 'gname', 'model', 'possession']:
                del info[agg_col]
    for bid in to_del:
        del dmp[bid]


def clean_vndb(dmp):
    pass


def merge_dump(egs, vndb):
    return dict()  # Don't care atm thx for asking
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


def write_structure(diff_dmp: DeepDiff, mode, skip=None, cv_path=None):
    # 'dictionary_item_added', 'values_changed', 'dictionary_item_removed'
    # root['\d+'] / root['\d+']['g']['\d+']
    # ['name'] = change / add, rem
    # ]['g'][ = release / brand

    if skip is None:
        skip = []

    def pretty(lod, indent=0):
        if len(lod) == 0:
            return 'None'
        return ('\n' + ' ' * indent).join(map(str, lod))

    badds = []
    gadds = []
    try:
        for level in diff_dmp['dictionary_item_added']:
            if 'g' in level.path(output_format='list'):
                gadds.append({'brand': level.up.up.t2['name'],
                              'id': level.path(output_format='list')[-1],
                              'name': level.t2['name']})
            else:
                badds.append({'id': level.path(output_format='list')[-1],
                              'name': level.t2['name']})
                for gid, info in level.t2['g'].items():
                    gadds.append({'brand': level.t2['name'],
                                  'id': gid,
                                  'name': info['name']})
    except KeyError as e:
        pass

    brems = []
    grems = []
    try:
        for level in diff_dmp['dictionary_item_removed']:
            if 'g' in level.path(output_format='list'):
                grems.append({'brand': level.up.up.t1['name'],
                              'id': level.path(output_format='list')[-1],
                              'name': level.t1['name']})
            else:
                brems.append({'id': level.path(output_format='list')[-1],
                              'name': level.t1['name']})
    except KeyError as e:
        pass

    bchgs = []
    gchgs = []
    try:
        for level in diff_dmp['values_changed']:
            if 'g' in level.path(output_format='list'):
                # using new brand name would be problematic in the case the brand name change gets skipped but game does not
                gchgs.append({'brand': level.up.up.up.t1['name'],
                              'id': level.path(output_format='list')[-2],
                              'old': level.t1,
                              'new': level.t2})
            else:
                bchgs.append({'id': level.path(output_format='list')[-2],
                              'old': level.t1,
                              'new': level.t2})
    except KeyError as e:
        pass

    double_trouble = False
    index = 0
    count = [[0, 0, 0], [0, 0, 0]]
    changes = [[[], [], []], [[], [], []]]
    skipped = set()
    finished = set()
    try:
        if len(brems) != 0:
            print('Brand deletions:')
            for b in brems:
                index += 1
                path = b['name']
                if index in skip:
                    skipped.add(path)
                    continue
                if mode == modes.NORMAL:
                    shutil.move(path, os.path.join('.Deleted', path))
                    changes[0][2].append(b)
                    print(f'{index}) Deleted 「 {path} 」')
                elif mode == modes.DRYRUN:
                    print(f'{index}) Delete 「 {path} 」')
                count[0][2] += 1
                finished.add(path)

        if len(grems) != 0:
            print('Game deletions:')
            for g in grems:
                index += 1
                path = os.path.join(g['brand'], g['name'])
                if index in skip:
                    if index in skip:
                        skipped.add(path)
                        continue
                if mode == modes.NORMAL:
                    shutil.move(path, os.path.join('.Deleted', path))
                    changes[1][2].append(g)
                    print(f'{index}) Deleted 「 {path} 」')
                elif mode == modes.DRYRUN:
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
                    opath = os.path.join(gchgs_c[i]['brand'], gchgs_c[i]['old'])
                    npath = os.path.join(gchgs_c[i]['brand'], gchgs_c[i]['new'])
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
                    if mode == modes.NORMAL:
                        shutil.move(opath, npath)
                        changes[1][1].append(gchgs_c[i])
                        print(f'{index}) Changed 「 {opath} 」 to 「 {npath} 」')
                    elif mode == modes.DRYRUN:
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
                    opath = bchgs_c[i]['old']
                    npath = bchgs_c[i]['new']
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
                    if mode == modes.NORMAL:
                        shutil.move(opath, npath)
                        changes[0][1].append(bchgs_c[i])
                        print(f'{index}) Changed 「 {opath} 」 to 「 {npath} 」')
                    elif mode == modes.DRYRUN:
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
            print('Brand additions:')
            for b in badds:
                path = b['name']
                index += 1
                if index in skip or path in skipped:
                    continue
                if mode == modes.NORMAL:
                    os.mkdir(path)
                    open(os.path.join(path, b['id']), 'w').close()
                    changes[0][0].append(b)
                    print(f'{index}) Created 「 {path} 」')
                elif mode == modes.DRYRUN:
                    print(f'{index}) Create 「 {path} 」')
                count[0][0] += 1

        if len(gadds) != 0:
            print('Game additions:')
            for g in gadds:
                path = os.path.join(g['brand'], g['name'])
                index += 1
                if index in skip or path in skipped:
                    continue
                if mode == modes.NORMAL:
                    os.mkdir(path)
                    open(os.path.join(path, g['id']), 'w').close()
                    changes[1][0].append(g)
                    print(f'{index}) Created 「 {path} 」')
                elif mode == modes.DRYRUN:
                    print(f'{index}) Create 「 {path} 」')
                count[1][0] += 1

    except Exception as e:
        try:
            if len(changes[1][0]) != 0:
                print('Rolling back game additions...')
                while len(changes[1][0]) != 0:
                    path = os.path.join(changes[1][0][-1]['brand'], changes[1][0][-1]['name'])
                    os.remove(os.path.join(path, changes[1][0][-1]['id']))
                    os.rmdir(path)
                    del changes[1][0][-1]

            if len(changes[0][0]) != 0:
                print('Rolling back brand additions...')
                while len(changes[0][0]) != 0:
                    path = changes[0][0][-1]['name']
                    os.remove(os.path.join(path, changes[0][0][-1]['id']))
                    os.rmdir(path)
                    del changes[0][0][-1]

            if len(changes[0][1]) != 0:
                print(f'Rolling back brand changes...')
                while len(changes[0][1]) != 0:
                    opath = changes[0][1][-1]['old']
                    npath = changes[0][1][-1]['new']
                    shutil.move(npath, opath)
                    del changes[0][1][-1]

            if len(changes[1][1]) != 0:
                print(f'Rolling back game changes...')
                while len(changes[1][1]) != 0:
                    opath = os.path.join(changes[1][1][-1]['brand'], changes[1][1][-1]['old'])
                    npath = os.path.join(changes[1][1][-1]['brand'], changes[1][1][-1]['new'])
                    shutil.move(npath, opath)
                    del changes[1][1][-1]

            if len(changes[1][2]) != 0:
                print('Rolling back game deletions...')
                while len(changes[1][2]) != 0:
                    path = os.path.join(changes[1][2][-1]['brand'], changes[1][2][-1]['name'])
                    shutil.move(os.path.join('.Deleted', path), path)
                    del changes[1][2][-1]

            if len(changes[0][2]) != 0:
                print(f'Rolling back brand deletions...')
                while len(changes[0][2]) != 0:
                    path = changes[0][2][-1]['name']
                    shutil.move(os.path.join('.Deleted', path), path)
                    del changes[0][2][-1]

        except Exception as e:
            print('An error occured while rolling back changes...（；ﾟдﾟ）ﾔﾍﾞｪ')
            double_trouble = True

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


def main():
    egs_user = None
    vndb_user = None

    def infer_dump(type):
        if type != dumps.EGS:
            return dict()  # don't care atm thx for asking

        print('Inferring previous dump data from folder structure...')
        dmp = dict()
        walkie = walklevel('.', depth=2)
        next(walkie)
        for dir, _, files in walkie:
            name = dir[2:]
            bid = next(filter(lambda x: '.' not in x, files), None)
            if bid is None:
                continue
            dmp[bid] = dict()
            dmp[bid]['name'] = name
            dmp[bid]['g'] = dict()
            talkie = walklevel(os.sep.join(['.', name]), depth=2)
            next(talkie)
            for dir2, _, files2 in talkie:
                title = dir2.split(name, maxsplit=1)[1]
                gid = next(filter(lambda x: '.' not in x, files2), None)
                if gid is None:
                    continue
                dmp[bid]['g'][gid] = dict()
                dmp[bid]['g'][gid]['name'] = title

        return dmp

    def read_dump(dump, user=None, prev_dump=False):
        if not isinstance(dump, dumps):
            raise TypeError
        if dump == dumps.EGS_VNDB:
            raise ValueError

        if prev_dump:
            choice = 0
        else:
            msg = f'{dump.name}:'
            choices = ['Use downloaded dump',
                       'Download latest dump and save it',
                       'Download latest dump but don\'t save it']
            choice = ask(msg, choices=choices)
            while not -1 < choice < 3:
                print()
                choice = ask(msg, choices=choices)

        if dump == dumps.VNDB:
            ls = list(VNDB_API.local_dumps(False))
        elif dump == dumps.EGS:
            ls = list(EGS_SQL.local_dumps('ubg'))

        if choice == 0 and len(ls) == 0:
            print(f'Couldn\'t find local {dump.name} dump.')
            if prev_dump:
                return dict()
            print('Falling back to downloading and saving...')
            choice = 1
        if choice == 0:
            if prev_dump:
                msg = 'Choose previous dump:'
                i = ask(msg, choices=ls, no_choice=True)
                while not -2 < i < len(ls):
                    i = ask(msg, choices=ls, no_choice=True)
                if i == -1:
                    return dict()
            else:
                msg = 'Choose current dump:'
                i = ask(msg, choices=ls, no_choice=False)
                while not -1 < i < len(ls):
                    i = ask(msg, choices=ls, no_choice=False)
            with open(ls[i], 'r', encoding='utf-8') as f:
                dmp = load(f)
        elif choice == 1 or choice == 2:
            if user is None:
                msg = f'{dump.name} user:'
                user = ask(msg)
            if dump == dumps.VNDB:
                dmp = VNDB_API.dump(user, False)
            elif dump == dumps.EGS:
                dmp = EGS_SQL.dump(user, 'ubg')
        if choice == 1:
            if dump == dumps.VNDB:
                VNDB_API.write_dump(False, dmp=dmp)
            elif dump == dumps.EGS:
                EGS_SQL.write_dump('ubg', dmp=dmp)
        return dmp

    if EGS_available and not bool(input('Use EGS? empty for Y anything for N\n>')):
        cdmp_egs = read_dump(dumps.EGS, user=egs_user)
        pdmp_egs = read_dump(dumps.EGS, prev_dump=True)
    else:
        cdmp_egs = dict()
        pdmp_egs = dict()

    cv_path = None
    if VNDB_available and bool(input('Use VNDB? empty for N anything for Y\n>')):
        cdmp_vndb = read_dump(dumps.VNDB, user=vndb_user)
        pdmp_vndb = read_dump(dumps.VNDB, prev_dump=True)
        if not bool(input('Create icons for folders? empty for Y anything for N\n>')):
            cv_path = input('VNDB covers dump path: leave empty to download covers\n>')
            if not cv_path:
                cv_path = None
    else:
        cdmp_vndb = dict()
        pdmp_vndb = dict()

    clean_egs(cdmp_egs)
    clean_egs(pdmp_egs)
    clean_vndb(cdmp_vndb)
    clean_vndb(pdmp_vndb)
    if len(cdmp_egs) != 0 and len(cdmp_vndb) != 0:
        cdmp = merge_dump(egs=cdmp_egs, vndb=cdmp_vndb)
        if len(pdmp_egs) != 0 and len(pdmp_vndb) != 0:
            pdmp = merge_dump(pdmp_egs, pdmp_vndb)
        else:
            pdmp = infer_dump(dumps.EGS_VNDB)
    elif len(cdmp_egs) != 0:
        cdmp = cdmp_egs
        if len(pdmp_egs) != 0:
            pdmp = pdmp_egs
        else:
            pdmp = infer_dump(dumps.EGS)
    elif len(cdmp_vndb) != 0:
        cdmp = cdmp_vndb
        if len(pdmp_vndb) != 0:
            pdmp = pdmp_vndb
        else:
            pdmp = infer_dump(dumps.VNDB)
    else:
        print('Requires either EGS or VNDB. Please provide.')
        input()
        return

    diff_dmp = DeepDiff(pdmp, cdmp, exclude_regex_paths=[r"root\['\d+']\['g']\['\d+']\['vid']",
                                                         r"root\['\d+']\['g']\['\d+']\['model']"], ignore_order=True,
                        view='tree')
    write_structure(diff_dmp, modes.DRYRUN, skip=skip, cv_path=cv_path)
    input()
    write_structure(diff_dmp, modes.NORMAL, skip=skip, cv_path=cv_path)
    input()


if __name__ == '__main__':
    main()
