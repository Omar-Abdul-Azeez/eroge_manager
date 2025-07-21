# -*- encoding:utf-8 -*-
import os
import sys
import regex
import logging

logger_module = logging.getLogger('eroge')

logger_io = logger_module.getChild('io')
logger_io.addHandler(logging.NullHandler())
def audit_os(event, args):
    if event.startswith('os.') or event == 'open':
        logger_io.debug('%s happened with args %s', event, args)

sys.addaudithook(audit_os)

from eroge.egs_sql import get_userlist


def walklevel(path, depth=1):
    """It works just like os.walk, but you can pass it a level parameter
           that indicates how deep the recursion will go.
           If depth is 1, the current directory is listed.
           If depth is 0, nothing is returned.
           If depth is -1 (or less than 0), the full depth is walked.
        """
    from os.path import sep
    from os import walk
    # If depth is negative, just walk
    # and copy dirs to keep consistent behavior for depth = -1 and depth = inf
    if depth < 0:
        for root, dirs, files in walk(path):
            yield root, dirs[:], files
        return
    elif depth == 0:
        return

    base_depth = path.rstrip(sep).count(sep)
    for root, dirs, files in walk(path):
        yield root, dirs[:], files
        cur_depth = root.count(sep)
        if base_depth + depth <= cur_depth:
            del dirs[:]


dquotes = [('「', '」'), ('『', '』'), ('“', '”')]
def special_chars(string, replace=False, dquotes=dquotes[2]):
    # \/:*?"<>|
    # WON'T REPLACE <> AND F NTFS (actually haven't encountered yet（；ﾟдﾟ）ｺﾁｺﾁ)
    if string.endswith('.'):
        # print(f'TRAILING PERIOD（；ﾟдﾟ）ﾋｨｨｨ Title: {string}')
        string = string[:-1]
    if replace:
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
    else:
        return ''.join([c for c in string if c not in {'\\', '/', ':', '*', '?', '"', '<', '>', '|'}])


def infer_dump(root='.'):
    dmp = {}
    walkie = walklevel(root, depth=1)
    next(walkie)
    for dir, _, files in walkie:
            folder = os.path.basename(dir)
            bid = next(filter(lambda x: regex.match(r'^\d+$', x) is not None, files), None)
            if bid is None:
                logger_module.warning('Couldn\'t identify 「%s」', folder)
                continue
            logger_module.debug('Identified 「%s」', folder)
            dmp[bid] = {'name': folder,
                        'g': {}}
            talkie = walklevel(os.path.join(root, folder), depth=1)
            next(talkie)
            for dir2, _, files2 in talkie:
                title = os.path.basename(dir2)
                gid = next(filter(lambda x: regex.match(r'^\d+$', x) is not None, files2), None)
                if gid is None:
                    logger_module.warning('Couldn\'t identify 「%s」の「%s」', folder, title)
                    continue
                logger_module.debug('Identified 「%s」の「%s」', folder, title)
                dmp[bid]['g'][gid] = {'name': title}
    return dmp


def clean_dump(dmp):
    del dmp['info']
    for b in list(dmp.keys()):
        dmp[b]['name'] = special_chars(dmp[b]['name'], replace=True)
        for g in list(dmp[b]['g'].keys()):
            if not dmp[b]['g'][g]['possession']:
                del dmp[b]['g'][g]
                continue
            dmp[b]['g'][g]['name'] = special_chars(dmp[b]['g'][g]['name'], replace=True)
            del dmp[b]['g'][g]['possession']
        if len(dmp[b]['g']) == 0:
            del dmp[b]
            continue


def write_structure(cdmp, ndmp, dmp_diff, eroge_root='.'):
    logger_module.info('Syncing library...')
    count = [[0, 0, 0], [0, 0, 0]]
    changes = [[[], [], []], [[], [], []]]

    if len(dmp_diff['removed_brands']) != 0:
        logger_module.info('Brand Removals:')
        for b in dmp_diff['removed_brands']:
            cpath = os.path.join(eroge_root, cdmp[b]['name'])
            npath = os.path.join(eroge_root, '!Removed!', cdmp[b]['name'])
            os.rename(cpath, npath)
            logger_module.info('Removed 「%s」', cdmp[b]['name'])
            changes[0][2].append(b)
            count[0][2] += 1

    if len(dmp_diff['changed_brands']) != 0:
        logger_module.info('Brand Changes:')
        for b in dmp_diff['changed_brands']:
            cpath = os.path.join(eroge_root, cdmp[b]['name'])
            npath = os.path.join(eroge_root, ndmp[b]['name'])
            os.rename(cpath, npath)
            cpath = os.path.join(eroge_root, '!Removed!', cdmp[b]['name'])
            npath = os.path.join(eroge_root, '!Removed!', ndmp[b]['name'])
            if os.path.exists(cpath):
                os.rename(cpath, npath)
            logger_module.info('Changed 「%s」 to 「%s」', cdmp[b]['name'], ndmp[b]['name'])
            changes[0][1].append(b)
            count[0][1] += 1

    if len(dmp_diff['added_brands']) != 0:
        logger_module.info('Brand Additions:')
        for b in dmp_diff['added_brands']:
            path = os.path.join(eroge_root, ndmp[b]['name'])
            if not os.path.exists(path):
                os.mkdir(path)
            open(os.path.join(path, b), 'w').close()
            changes[0][0].append(b)
            logger_module.info('Created 「%s」', ndmp[b]['name'])
            count[0][0] += 1

    if len(dmp_diff['removed_games']) != 0:
        logger_module.info('Game Removals:')
        for b, lg in dmp_diff['removed_games']:
            for g in lg:
                cpath = os.path.join(eroge_root, ndmp[b]['name'], cdmp[b]['g'][g]['name'])
                npath = os.path.join(eroge_root, '!Removed!', ndmp[b]['name'], cdmp[b]['g'][g]['name'])
                os.rename(cpath, npath)
                changes[1][2].append((b, g))
                logger_module.info('Removed 「%s」の「%s」', ndmp[b]['name'], cdmp[b]['g'][g]['name'])
                count[1][2] += 1

    if len(dmp_diff['changed_games']) != 0:
        logger_module.info('Game Changes:')
        for b, lg in dmp_diff['changed_games']:
            for g in lg:
                cpath = os.path.join(eroge_root, ndmp[b]['name'], cdmp[b]['g'][g]['name'])
                npath = os.path.join(eroge_root, ndmp[b]['name'], ndmp[b]['g'][g]['name'])
                os.rename(cpath, npath)
                changes[1][1].append((b, g))
                logger_module.info('Changed 「%s」の「%s」 to 「%s」', ndmp[b]['name'], cdmp[b]['g'][g]['name'], ndmp[b]['g'][g]['name'])
                count[1][1] += 1

    if len(dmp_diff['added_games']) != 0:
        logger_module.info('Game Additions:')
        for b, lg in dmp_diff['added_games']:
            for g in lg:
                path = os.path.join(eroge_root, ndmp[b]['name'], ndmp[b]['g'][g]['name'])
                if not os.path.exists(path):
                    os.mkdir(path)
                open(os.path.join(path, g), 'w').close()
                changes[1][0].append((b, g))
                logger_module.info('Added 「%s」の「%s」', ndmp[b]["name"], ndmp[b]["g"][g]["name"])
                count[1][0] += 1
    s = 'Totals:' \
       f'{count[0][0]} Brand Additions' \
       f'\n{count[0][1]} Brand Changes' \
       f'\n{count[0][2]} Brand Removals' \
       f'\n{count[1][0]} Game Additions' \
       f'\n{count[1][1]} Game Changes' \
       f'\n{count[1][2]} Game Removals'
    print(s)
    logger_module.info(s)


def diff(cdmp, ndmp):
    cur = set(cdmp)
    nw = set(ndmp)
    mut = cur.intersection(nw)
    res = {'added_brands': nw.difference(cur),
           'removed_brands': cur.difference(nw),
           'changed_brands': [],
           'added_games': [],
           'removed_games': [],
           'changed_games': []}
    res['added_games'] = [(b, set(ndmp[b]['g'])) for b in res['added_brands']]
    for b in mut:
        if cdmp[b]['name'] != ndmp[b]['name']:
            res['changed_brands'].append(b)
        curg = set(cdmp[b]['g'])
        nwg = set(ndmp[b]['g'])
        mutg = curg.intersection(nwg)
        res['added_games'].append((b, nwg.difference(curg)))
        res['removed_games'].append((b, curg.difference(nwg)))
        res['changed_games'].append((b, (g for g in mutg if cdmp[b]['g'][g]['name'] != ndmp[b]['g'][g]['name'])))

    return res


def sync_backlog(eroge_root='.', dump_root='.', offline=False, user=None, dump=True):
    cdmp = infer_dump(eroge_root)
    ndmp = get_userlist(root=dump_root, offline=offline, user=user, dump=dump)
    clean_dump(ndmp)
    write_structure(cdmp=cdmp, ndmp=ndmp, dmp_diff=diff(cdmp, ndmp), eroge_root=eroge_root)
