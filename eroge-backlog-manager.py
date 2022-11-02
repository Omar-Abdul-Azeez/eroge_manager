# -*- encoding:utf-8 -*-
import os
import operator
import platform
import shutil
from functools import reduce
import natsort
import json
from pil import Image, ImageOps
import cfscrape
import VNDB_API
import EGS_SQL
from enum import Enum

class dumps(Enum):
    VNDB = 1
    EGS = 2

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
sg = {}
sb = {}
sv = {'v3182': 'SHANGRLIA'}
sr = {}
# MODES: 1 = exec, 2 = dry run skip
MODE = 2
skip_lines = []
skip_str = ''
# parse skip_str
if skip_str != '':
    ls = skip_str.split(' ')
    for i in range(len(ls)):
        if '-' in ls[i]:
            spl = ls[i].split('-')
            skip_lines.append(range(int(spl[0]), int(spl[1])+1))
        else:
            skip_lines.append(int(ls[i]))


def special_chars_to_full_width(string, dquotes=dquotes[2]):
    # \/:*?"<>|
    # WON'T REPLACE <> NOR TRAILING PERIODS AND F NTFS (actually haven't encountered yet（；ﾟдﾟ）)
    if string[-1] == '.':
        print(f'TRAILING PERIOD（；ﾟдﾟ） Title: {string}')
        input()
        raise ValueError
    lis = []
    flag = False
    for c in string:
        if c == '<' or c == '>':
            print(f'<> IN TITLE（；ﾟдﾟ） Title: {string}')
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


def special_brand_title(id):
    return sb.get(id)


def special_game_title(id):
    return sg.get(id)


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


def ready_dump(dmp_egs=None, dmp_vndb=None):
    if not (dmp_egs or dmp_vndb):
        raise ValueError
    elif dmp_egs and dmp_vndb:
        pass # don't care atm thx for asking
    elif dmp_egs:
        to_del = []
        for bid, info in dmp_egs.items():
            i = 0
            while i < len(info['gid']):
                if info['possession'][i]:
                    tmp = special_brand_title(bid)
                    if tmp is None:
                        info['bname'][i] = special_chars_to_full_width(info['bname'][i])
                    else:
                        info['bname'][i] = tmp
                    tmp = special_game_title(info['gname'][i])
                    if tmp is None:
                        info['gname'][i] = special_chars_to_full_width(info['gname'][i])
                    else:
                        info['gname'][i] = tmp
                    i += 1
                    continue
                elif info['possession'][i] is None:
                    print(f'"possession = None" met! - Title: {info["gname"][i]}')
                for agg_col in ['gid', 'vid', 'gname', 'model', 'possession']:
                    del info[agg_col][i]
            if len(info['gid']) == 0:
                to_del.append(bid)
        for bid in to_del:
            del dmp_egs[bid]
    elif dmp_vndb:
        pass # don't care atm thx for asking

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


def write_structure(dmp_egs=None, dmp_vndb=None, icons=False, prev_db=None, cv_path=None):
    #   mk,ln(src,dst) rename src     rename dst   icons
    # ( ([], [], []) , ([], [], []) , ([], [], []) , [])
    dirs = (([], [], []), ([], [], []), ([], [], []), [])
    dels = []
    multirelease_edits = ([], [])

    def mk_cover(game, id, cv, url):
        path = f'{game}{os.sep}'
        if cv_path:
            if os.path.exists(f'{path}{id}.jpg'):
                os.remove(f'{path}{id}.jpg')
            shutil.copyfile(f'{cv_path}{os.sep}{cv[-2:]}{os.sep}{cv[2:]}.jpg', f'{path}{id}.jpg')
        else:
            cv_img = cfscrape.create_scraper().get(url)
            cv_img.decode_content = True
            if os.path.exists(f'{path}{id}.jpg'):
                os.remove(f'{path}{id}.jpg')
            with open(f'{path}{id}.jpg', 'wb') as f:
                f.write(cv_img.content)
        img = Image.open(f'{path}{id}.jpg').convert('RGBA')
        hsz = 256
        perc = (hsz/float(img.size[1]))
        wsz = int((float(img.size[0])*float(perc)))
        img = img.resize((wsz, hsz), Image.LANCZOS)
        bg = hsz if hsz > wsz else wsz
        nw = Image.new('RGBA', (bg,bg), (0, 0, 0, 0))
        offset = (int(round(((bg-wsz) / 2), 0)), int(round(((bg-hsz) / 2), 0)))
        nw.paste(img, offset)
        if os.path.exists(f'{path}{id}.ico'):
            os.remove(f'{path}{id}.ico')
        nw.save(f'{path}{id}.ico')
        img.close()
        nw.close()
        if os.path.exists(f'{path}desktop.ini'):
            os.remove(f'{path}desktop.ini')
        if platform.system() == 'Windows':
            try:
                with open(f'{path}desktop.ini', 'w', encoding='ANSI') as f:
                    f.write('[.ShellClassInfo]\nConfirmFileOp=0\n')
                    f.write(f'IconResource={id}.ico,0')
                    f.write(f'\nIconFile={id}.ico\nIconIndex=0')
            except UnicodeEncodeError as e:
                with open(f'{path}desktop.ini', 'w', encoding='utf-8') as f:
                    f.write('[.ShellClassInfo]\nConfirmFileOp=0\n')
                    f.write(f'IconResource={id}.ico,0')
                    f.write(f'\nIconFile={id}.ico\nIconIndex=0')
            os.system(f'attrib +r "{game}"')
            os.system(f'attrib +h "{path}desktop.ini"')
            os.system(f'attrib +h "{path}{id}.ico"')
        elif platform.system() == 'Linux':
            try:
                with open(f'{path}desktop.ini', 'w+', encoding='iso_8859_1') as f:
                    f.write('[.ShellClassInfo]\nConfirmFileOp=0\n')
                    f.write(f'IconResource={id}.ico,0')
                    f.write(f'\nIconFile={id}.ico\nIconIndex=0')
            except UnicodeEncodeError as e:
                with open(f'{path}desktop.ini', 'w', encoding='utf-8') as f:
                    f.write('[.ShellClassInfo]\nConfirmFileOp=0\n')
                    f.write(f'IconResource={id}.ico,0')
                    f.write(f'\nIconFile={id}.ico\nIconIndex=0')
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
        if os.sep not in dir:
            ls = next(os.walk(dir))
            if len(set(ls[1]) - {'Extras'}) == 0 and len(set(ls[2]) - {'desktop.ico', f'{dir}.ico', f'{dir}.jpg'}) == 0:
                mv_dir(dir, f'Deleted{os.sep}{dir}')
        else:
            mv_dir(dir, f'Deleted{os.sep}{dir}')

    for v in db:
        if prev_db:
            ind = [i for i in range(len(prev_db)) if prev_db[i]['id'] == v['id']]
            if len(ind) == 0:
                v_old = None
            else:
                v_old = prev_db.pop(ind[0])
        else:
            v_old = None
        if not v_old:
            dirs[0][0].append(v['title'])
            dirs[0][0].append(os.sep.join(('Extras', v['title'])))
            dirs[3].append([v['title'], v['id'], *v['cover']])
            for r in v['releases']:
                if len(r['vns']) > 1:
                    if r['patch']:
                        dirs[0][1].append(os.sep.join(('Shared releases', 'Patches', r['platform'], r['title'])))
                        dirs[0][2].append(os.sep.join((v['title'], 'Patches', r['platform'], r['title'])))
                    else:
                        dirs[0][1].append(os.sep.join(('Shared releases', r['platform'], r['title'])))
                        dirs[0][2].append(os.sep.join((v['title'], r['platform'], r['title'])))
                else:
                    if v['patch']:
                        dirs[0][0].append(os.sep.join((v['title'], 'Patches', r['platform'], r['title'])))
                    else:
                        dirs[0][0].append(os.sep.join((v['title'], r['platform'], r['title'])))
        elif v['title'] == v_old['title']:
            pass
        else:
            if v['multirelease'] != v_old['multirelease']:
                print(f"Can't handle edit of {v_old['title_v']}/{v_old['title_r']} to {v['title_v']}/{v['title_r']} with different multirelease flags!")
                continue
            if v['title_v'] not in dirs[2][0]:
                dirs[1][0].append(v_old['title_v'])
                dirs[2][0].append(v['title_v'])
                if icons and (v['cv'] != v_old['cv'] or v['title_v'] != v_old['title_v']):
                    dirs[3].append((v['title_v'], v['cv']))
                dirs[1][0].append(os.sep.join((v_old['title_v'], 'Extras')))
                dirs[2][0].append(os.sep.join((v['title_v'], 'Extras')))
            if v['multirelease']:
                if v['patch']:
                    dirs[1][1].append(os.sep.join(('Shared releases', 'Patches', v_old['lang'], v_old['platform'], v_old['title_r'])))
                    dirs[2][1].append(os.sep.join(('Shared releases', 'Patches', v['lang'], v['platform'], v['title_r'])))
                    dirs[1][2].append(os.sep.join((v_old['title_v'], 'Patches', v_old['lang'], v_old['platform'], v_old['title_r'])))
                    dirs[2][2].append(os.sep.join((v['title_v'], 'Patches', v['lang'], v['platform'], v['title_r'])))
                else:
                    dirs[1][1].append(os.sep.join(('Shared releases', v_old['lang'], v_old['platform'], v_old['title_r'])))
                    dirs[2][1].append(os.sep.join(('Shared releases', v['lang'], v['platform'], v['title_r'])))
                    dirs[1][2].append(os.sep.join((v_old['title_v'], v_old['lang'], v_old['platform'], v_old['title_r'])))
                    dirs[2][2].append(os.sep.join((v['title_v'], v['lang'], v['platform'], v['title_r'])))
            else:
                if v['patch']:
                    dirs[1][0].append(os.sep.join((v_old['title_v'], 'Patches', v_old['lang'], v_old['platform'], v_old['title_r'])))
                    dirs[2][0].append(os.sep.join((v['title_v'], 'Patches', v['lang'], v['platform'], v['title_r'])))
                else:
                    dirs[1][0].append(os.sep.join((v_old['title_v'], v_old['lang'], v_old['platform'], v_old['title_r'])))
                    dirs[2][0].append(os.sep.join((v['title_v'], v['lang'], v['platform'], v['title_r'])))
    if prev_db:
        for v_old in prev_db:
            if v_old['title_v'] not in dels:
                dels.append(v_old['title_v'])
            if v_old['multirelease']:
                if v_old['patch']:
                    dels.append(os.sep.join((v_old['title_v'], 'Patches', v_old['lang'], v_old['platform'], v_old['title_r'])))
                else:
                    dels.append(os.sep.join((v_old['title_v'], v_old['lang'], v_old['platform'], v_old['title_r'])))
            else:
                if v_old['patch']:
                    dels.append(os.sep.join((v_old['title_v'], 'Patches', v_old['lang'], v_old['platform'], v_old['title_r'])))
                else:
                    dels.append(os.sep.join((v_old['title_v'], v_old['lang'], v_old['platform'], v_old['title_r'])))
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
    if not os.path.exists(os.sep.join(('Extras', 'Shared extras'))):
        mk_dir(os.sep.join(('Extras', 'Shared extras')))
    if MODE == 1:
        for v in dels:
            if os.path.exists(v):
                rm_dir(v)
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
                    multirelease_edits[0].append(dirs[1][1][i])
                    multirelease_edits[1].append(dirs[2][1][i])
            else:
                if not os.path.exists(dirs[2][2][i]):
                    mk_dir(dirs[2][1][i], sym=dirs[2][2][i])
                    count[0] += 1
        for v in dirs[0][0]:
            if not os.path.exists(v):
                mk_dir(v)
                count[0] += 1
        for i in range(len(dirs[0][1])):
            if not os.path.exists(dirs[0][2][i]):
                mk_dir(dirs[0][1][i], sym=dirs[0][2][i])
                count[0] += 1
        for v in dirs[3]:
            mk_cover(*v)
    elif MODE == 2:
        while True:
            counter = [0, 0, 0]
            if flag:
                print('Deleting...')
            else:
                print('DELETIONS:')
            for v in dels:
                if os.path.exists(v):
                    counter[2] += 1
                    if sum(counter) in skip_lines:
                        continue
                    if flag:
                        rm_dir(v)
                        count[2] += 1
                    else:
                        print(f'{sum(counter)})  {v}')
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
                            multirelease_edits[0].append(dirs[1][1][i])
                            multirelease_edits[1].append(dirs[2][1][i])
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
            for g in dirs[0][0]:
                if not os.path.exists(g):
                    counter[0] += 1
                    if sum(counter) in skip_lines:
                        continue
                    if flag:
                        mk_dir(g)
                        count[0] += 1
                    else:
                        print(f'{sum(counter)})  {g}')
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
            if flag and icons:
                for c in dirs[3]:
                    mk_cover(*c)
            if not flag:
                nl = '\n'
                if input(f'Execute {counter[0]} creations and {counter[1]} edits and {counter[2]} deletions?\nMultirelease edits:\n{nl.join([" -> ".join(x) for x in zip(multirelease_edits[0], multirelease_edits[1])])}\n>'):
                    flag = True
            else:
                break
    nl = '\n'
    print(f'Created {count[0]} and edited {count[1]} and deleted {count[2]}!\nPlease check these for any dead links:\n{nl.join([" -> ".join(x) for x in zip(multirelease_edits[0], multirelease_edits[1])])}')


def main():

    def read_dump(dump: dumps, prev_dump=False):
        if not isinstance(dump, dumps):
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

        ls = natsort.natsorted(next(os.walk('.'))[2])
        if dump == dumps.VNDB:
            ls = list(filter(lambda x: 'vndb' in x and 'json' in x and 'full_backup' not in x, ls))
        elif dump == dumps.EGS:
            ls = list(filter(lambda x: 'egs' in x and 'json' in x and 'bg' in x, ls))

        if choice == 0 and len(ls) == 0:
            print(f'Couldn\'t find local {dump.name} dump.')
            if prev_dump:
                print('Won\'t use a previous dump.')
                return None
            print('Falling back to downloading and saving.')
            choice = 1
        if choice == 0:
            if prev_dump:
                msg = 'Choose previous dump:'
                i = ask(msg, choices=ls, no_choice=True)
                while not -2 < i < len(ls):
                    i = ask(msg, choices=ls, no_choice=True)
                if i == -1:
                    return None
            else:
                msg = 'Choose current dump'
                i = ask(msg, choices=ls, no_choice=False)
                while not -1 < i < len(ls):
                    i = ask(msg, choices=ls, no_choice=False)
            with open(ls[i], 'r', encoding='utf-8') as f:
                dmp = json.load(f)
        elif choice == 1 or choice == 2:
            if dump == dumps.VNDB:
                dmp = VNDB_API.dump(False)
            elif dump == dumps.EGS:
                dmp = EGS_SQL.dump('ubg')
        if choice == 1:
            if dump == dumps.VNDB:
                VNDB_API.write_dump(False, dmp=dmp)
            elif dump == dumps.EGS:
                EGS_SQL.write_dump('ubg', dmp=dmp)
        return dmp

    cdmp_egs = None
    pdmp_egs = None
    if not bool(input('Use EGS? empty for Y anything for N\n>')):
        cdmp_egs = read_dump(dumps.EGS)
        pdmp_egs = read_dump(dumps.EGS, prev_dump=True)

    cv_path = None
    cdmp_vndb = None
    pdmp_vndb = None
    if bool(input('Use VNDB? empty for N anything for Y\n>')):
        cdmp_vndb = read_dump(dumps.VNDB)
        pdmp_vndb = read_dump(dumps.VNDB, prev_dump=True)
        if not bool(input('Create icons for folders? empty for Y anything for N\n>')):
            cv_path = input('VNDB covers dump path: leave empty to download covers\n>')
            if not cv_path:
                cv_path = None

    ready_dump(dmp_egs=cdmp_egs, dmp_vndb=cdmp_vndb)
    ready_dump(dmp_egs=pdmp_egs, dmp_vndb=pdmp_vndb)
    write_structure(dbc, icons, prev_db=dbp, cv_path=cv_path)
    input()


if __name__ == '__main__':
    main()