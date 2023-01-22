# -*- encoding:utf-8 -*-
import json
from os.path import join, splitext

import regex
import requests
from bs4 import BeautifulSoup
from natsort import natsorted

import eroge.helper as helper
from eroge.trackers.rules import now, _FORMAT_SAVE, _PATTERN_SAVE


"""
    gb = game + brand
    bg = brand + array_agg(game)
    u = userlist(gid + possession)だけ
    ugb = userlistの game + brand
    ubg = userlistの brand + array_agg(game)
    ugrgb = userlistの group + array_agg(game) + array_agg(brand)
    kankei = kankei WHERE kind IN ('apend','bundling')
    ugbkankei = userlistの game + brand + array_agg(bundle_of) + array_agg(append_to) + array_agg(bundled_in) + array_agg(appends)
"""

FORMAT_SAVE = _FORMAT_SAVE.replace('{tracker}', 'egs')
PATTERN_SAVE = _PATTERN_SAVE.replace('{tracker}', 'egs')
TABLES = {'u', 'gb', 'ugb', 'bg', 'ubg', 'ugrgb', 'kankei', 'ugbkankei'}
AGG_TABLES = {'bg', 'ubg', 'ugrgb', 'ugbkankei'}
AGG_COLS = {'gid', 'vid', 'gname', 'model', 'bid', 'bname', 'bundled_in', 'bundle_of', 'appends', 'append_to'}
SQL = """WITH
    gb AS (SELECT gamelist.id as gid,
                  gamelist.vndb as vid,
                  gamename as gname,
                  brandlist.id as bid,
                  brandlist.brandname as bname
             FROM gamelist
             INNER JOIN brandlist
                 ON brandlist.id = gamelist.brandname
             ORDER BY gid
           ),
    bg AS (SELECT brandlist.id as bid,
                  brandlist.brandname as bname,
                  array_agg(gamelist.id) as gid,
                  array_agg(gamelist.vndb) as vid,
                  array_agg(gamename) as gname,
                  array_agg(model) as model
             FROM brandlist
             INNER JOIN gamelist
                 ON gamelist.brandname = brandlist.id
             GROUP BY bid,
                      bname
             ORDER BY bid
           ),
    u AS (SELECT game,
                 possession
            FROM userreview
                WHERE uid = '{user}'
            ORDER BY game
         ),
    ugb AS (SELECT gamelist.id as gid,
                   gamelist.vndb as vid,
                   gamename as gname,
                   brandlist.id as bid,
                   brandlist.brandname as bname,
                   model,
                   possession
              FROM u
              INNER JOIN gamelist
                   ON gamelist.id = u.game
              INNER JOIN brandlist
                   ON brandlist.id = gamelist.brandname
              ORDER BY gid
            ),
    ubg AS (SELECT bid,
                   bname,
                   array_agg(gid) as gid,
                   array_agg(vid) as vid,
                   array_agg(gname) as gname,
                   array_agg(model) as model,
                   array_agg(possession) as possession
              FROM ugb
              GROUP BY bid,
                       bname
              ORDER BY bid
           ),
    ugrgb AS (SELECT gamegrouplist.id as grid,
                     name as grname,
                     array_agg(gid) as gid,
                     array_agg(vid) as vid,
                     array_agg(gname) as gname,
                     array_agg(bid) as bid,
                     array_agg(bname) as bname,
                     array_agg(model) as model,
                     array_agg(possession) as possession
                FROM belong_to_gamegroup_list
                INNER JOIN gamegrouplist
                    ON gamegrouplist.id = gamegroup
                INNER JOIN ugb
                    ON gid = game
                GROUP BY grid
                ORDER BY grid
             ),
    kankei AS (SELECT id,
                      game_subject,
                      game_object,
                      kind
                 FROM connection_between_lists_of_games
                     WHERE kind IN ('apend','bundling')
                 ORDER BY id
              ),
    ugbkankei AS (SELECT gid,
                         vid,
                         gname,
                         bid,
                         bname,
                         model,
                         possession,
                         array_remove(array_agg(CASE
                                                WHEN kan_ob.kind = 'bundling'
                                                THEN kan_ob.game_subject
                                                ELSE NULL
                                                END
                                                )
                                      , NULL) as bundle_of,
                         array_remove(array_agg(CASE
                                                WHEN kan_sub.kind = 'bundling'
                                                THEN kan_sub.game_object
                                                ELSE NULL
                                                END)
                                      , NULL) as bundled_in,
                         array_remove(array_agg(CASE
                                                WHEN kan_sub.kind = 'apend'
                                                THEN kan_sub.game_object
                                                ELSE NULL
                                                END)
                                      , NULL) as append_to,
                         array_remove(array_agg(CASE
                                                WHEN kan_ob.kind = 'apend'
                                                THEN kan_ob.game_subject
                                                ELSE NULL
                                                END)
                                      , NULL) as appends
                    FROM ugb
                    LEFT OUTER JOIN kankei AS kan_ob
                        ON kan_ob.game_object = gid AND kan_ob.game_subject IN (SELECT gid from ugb)
                    LEFT OUTER JOIN kankei AS kan_sub
                        ON kan_sub.game_subject = gid AND kan_sub.game_object IN (SELECT gid FROM ugb)
                    GROUP BY gid,
                             vid,
                             gname,
                             bid,
                             bname,
                             model,
                             possession
                    ORDER BY bundle_of DESC,
                             append_to DESC,
                             bundled_in DESC,
                             appends DESC,
                             gid
                 )

    SELECT * FROM {table}"""


def local_dumps(table, dump_root):
    return natsorted(filter(lambda x: regex.match(PATTERN_SAVE.replace('{extra}', f'-{table}'), splitext(x)[0]) is not None,
                            next(helper.walklevel(dump_root))[2]), reverse=True)


def ask_table():
    return helper.ask("gb = game + brand\n"
                       "bg = brand + array_agg(game)\n"
                       "u = userlist(gid + possession)だけ\n"
                       "ugb = userlistの game + brand\n"
                       "ubg = userlistの brand + array_agg(game)\n"
                       "ugrgb = userlistの group + array_agg(game) + array_agg(brand)\n"
                       "kankei = kankei WHERE kind IN ('apend','bundling')\n"
                       "ugbkankei = userlistの game + brand + array_agg(bundle_of) + array_agg(append_to) + array_agg(bundled_in) + array_agg(appends)\n"
                       "SQL Table:", choices=TABLES)


def dl_dump(user, table=None):
    if table is None:
        table = ask_table()
    elif table not in TABLES:
        raise ValueError
    sql = SQL.format(user=user, table=table)
    r = requests.post("https://erogamescape.dyndns.org/~ap2/ero/toukei_kaiseki/sql_for_erogamer_form.php",
                      data={"sql": sql})

    soup = BeautifulSoup(r.content, features='html.parser')
    tbl = soup.find('div', attrs={'id': 'query_result_main'}).find('table')
    rows = iter(tbl)
    next(rows)
    headers = [col.text for col in next(rows)]
    dmp = [FORMAT_SAVE.format(extra=f'-{table}', TIME=now())]
    for row in rows:
        if row == '\n':
            continue
        values = [col.text for col in row]
        dmp.append(dict(zip(headers, values)))
        if table in AGG_TABLES:
            try:
                s = dmp[-1]['possession']
                if s[0] == '{' and s[-1] == '}':
                    dmp[-1]['possession'] = list(
                        map(lambda x: True if x == 't' else False if x == 'f' else None, s[1:-1].split(',')))
            except KeyError:
                pass
            for agg_col in AGG_COLS:
                try:
                    s = dmp[-1][agg_col]
                    if s.startswith('{') and s.endswith('}'):
                        tmp = s[1:-1].split(',')
                        i = 0
                        while i < len(tmp):
                            if tmp[i] == 'NULL':
                                tmp[i] = None
                            elif ' ' in tmp[i] and tmp[i].startswith('"') and tmp[i].endswith('"'):
                                tmp[i] = tmp[i][1:-1]
                            elif ' ' in tmp[i] and tmp[i].startswith('"'):  # element was split due to ',' inside it
                                try:
                                    tmp[i + 1] = tmp[i] + tmp[i + 1]  # add it to the next element and deal with it then
                                    del tmp[i]
                                    continue
                                except IndexError as e:
                                    pass
                            i += 1
                        dmp[-1][agg_col] = tmp
                except KeyError:
                    pass
    return dmp


def write_dump(dump_root, user=None, table=None, dmp=None):
    if dmp is None and (user is None or table is None):
        raise ValueError
    if dmp is None:
        dmp = dl_dump(user, table)
    with open(join(dump_root, dmp[0] + '.json'), 'w', encoding='utf-8') as f:
        json.dump(dmp, f, ensure_ascii=False)


def get_dump(dump_root, table='ubg', user=None, none=False):
    ls = list(local_dumps(table, dump_root=dump_root))
    if user:
        ls.insert(0, 'Download latest dump')
    if len(ls) == 0:
        return None
    else:
        ans = helper.ask('Choose dump:', choices=ls, show=True, none=none)
        if ans is None:
            return None
        elif ans == 'Download latest dump':
            dmp = dl_dump(user, table)
            write_dump(dmp=dmp, dump_root=dump_root)
            return dmp
        else:
            with open(join(dump_root, ans), 'r', encoding='utf-8') as f:
                return json.load(f)
