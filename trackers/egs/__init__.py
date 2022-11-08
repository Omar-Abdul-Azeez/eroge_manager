# -*- encoding:utf-8 -*-
import json
from datetime import datetime
from os.path import join

import regex
import requests
from bs4 import BeautifulSoup
from natsort import natsorted

from ... import helper


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
__TABLES = {'u', 'gb', 'ugb', 'bg', 'ubg', 'ugrgb', 'kankei', 'ugbkankei'}
__AGG_TABLES = {'bg', 'ubg', 'ugrgb', 'ugbkankei'}
__AGG_COLS = {'gid', 'vid', 'gname', 'model', 'bid', 'bname', 'bundled_in', 'bundle_of', 'appends', 'append_to'}
__DATE_FORMAT = '%Y-%m-%dT%H%M%SZ'
__SAVE_FORMAT = 'EGS-{table}-{date}'
__REGEX_PATTERN = r'$EGS-{table}-\d{4}(-\d\d){2}T\d{6}Z\.json^'
__SQL = """WITH
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


def dump(user, table):
    if table not in __TABLES:
        raise ValueError
    sql = __SQL.format(user=user, table=table)
    r = requests.post("https://erogamescape.dyndns.org/~ap2/ero/toukei_kaiseki/sql_for_erogamer_form.php",
                      data={"sql": sql})

    soup = BeautifulSoup(r.content, features='html.parser')
    table = soup.find('div', attrs={'id': 'query_result_main'}).find('table')
    rows = iter(table)
    next(rows)
    headers = [col.text for col in next(rows)]
    dmp = [__SAVE_FORMAT.format(table=table, date=datetime.utcnow().strftime(__DATE_FORMAT))]
    for row in rows:
        if row == '\n':
            continue
        values = [col.text for col in row]
        dmp.append(dict(zip(headers, values)))
        if table in __AGG_TABLES:
            try:
                s = dmp[-1]['possession']
                if s[0] == '{' and s[-1] == '}':
                    dmp[-1]['possession'] = list(
                        map(lambda x: True if x == 't' else False if x == 'f' else None, s[1:-1].split(',')))
            except KeyError:
                pass
            for agg_col in __AGG_COLS:
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


def write_dump(user=None, table=None, dmp=None, root='.'):
    if (user is None or table is None) and dmp is None:
        raise ValueError
    if dmp is None:
        dmp = dump(user, table)
    with open(join(root, dmp[0] + '.json'), 'w', encoding='utf-8') as f:
        json.dump(dmp, f, ensure_ascii=False)


def local_dumps(table, root='.'):
    return natsorted(filter(lambda x: regex.match(__REGEX_PATTERN.replace('{table}', table), x) is not None,
                            next(helper.walklevel(root))[2]))


def get_dump(table, root='.', can_dl=False, user=None, none=False):
    ls = list(local_dumps(table, root=root))
    if can_dl:
        ls.append('Download latest dump')
    if len(ls) == 0:
        return None
    else:
        ans = helper.ask('Choose dump:', choices=ls, show=True, none=none)
        if ans is None:
            return None
        elif ans == 'Download latest dump':
            if user is None:
                user = helper.ask('user:')
            return dump(user, table)
        else:
            with open(ans, 'r', encoding='utf-8') as f:
                return json.load(f)


def ask_table():
    return helper.ask("gb = game + brand\n"
                       "bg = brand + array_agg(game)\n"
                       "u = userlist(gid + possession)だけ\n"
                       "ugb = userlistの game + brand\n"
                       "ubg = userlistの brand + array_agg(game)\n"
                       "ugrgb = userlistの group + array_agg(game) + array_agg(brand)\n"
                       "kankei = kankei WHERE kind IN ('apend','bundling')\n"
                       "ugbkankei = userlistの game + brand + array_agg(bundle_of) + array_agg(append_to) + array_agg(bundled_in) + array_agg(appends)\n"
                       "SQL Table:", choices=__TABLES)

