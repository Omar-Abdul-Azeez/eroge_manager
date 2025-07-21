# -*- encoding:utf-8 -*-
import logging
import json
import os

import regex
from bs4 import BeautifulSoup
from natsort import natsorted

logger_egs = logging.getLogger(__name__)
logger_egs.addHandler(logging.NullHandler())

from eroge.network import request
from eroge.rules import format_save, pattern_save


"""
    g = game + brand
    b = brand
    u = userlist(gid + possession)だけ
    ug = userlistの game + brand
    ub = userlistの brand + array_agg(game)
"""


TABLES = {'u', 'g', 'ug', 'b', 'ub'}
SQL = """WITH
    g AS (SELECT gamelist.id as gid,
                 gamename as gname,
                 CASE WHEN dmm_genre='digital' AND dmm_genre_2='pcgame'
                       THEN 'https://pics.dmm.co.jp/digital/pcgame/' || dmm || '/' || dmm || 'pl.jpg'
                      WHEN dmm_genre='digital' AND dmm_genre_2='doujin'
                       THEN 'https://doujin-assets.dmm.co.jp/digital/game/' || dmm || '/' || dmm || 'pr.jpg'
                      WHEN dmm_genre='mono' AND dmm_genre_2='pcgame'
                       THEN 'https://pics.dmm.co.jp/mono/game/' || dmm || '/' || dmm || 'pl.jpg'
                      WHEN dlsite_id IS NOT NULL AND (dlsite_domain='pro' OR dlsite_domain='soft')
                       THEN 'https://img.dlsite.jp/modpub/images2/work/professional/' || left(dlsite_id,2) || LPAD(CAST(CAST(RIGHT(LEFT(dlsite_id, 5), 3) AS INTEGER) + 1 AS TEXT), 3, '0') || '000/' || dlsite_id || '_img_main.jpg'
                      WHEN dlsite_id IS NOT NULL
                       THEN 'https://img.dlsite.jp/modpub/images2/work/doujin/' || left(dlsite_id,2) || LPAD(CAST(CAST(RIGHT(LEFT(dlsite_id, 5), 3) AS INTEGER) + 1 AS TEXT), 3, '0') || '000/' || dlsite_id || '_img_main.jpg'
                      WHEN dmm IS NOT NULL
                       THEN 'https://pics.dmm.co.jp/mono/game/' || dmm || '/' || dmm || 'pl.jpg'
                      WHEN surugaya_1 IS NOT NULL AND surugaya_1 != 0
                       THEN 'https://www.suruga-ya.jp/database/pics/game/' || surugaya_1 || '.jpg'
                      ELSE '' END AS thumbnail_url,
                 brandlist.id as bid,
                 brandlist.brandname as bname
            FROM gamelist
            INNER JOIN brandlist
                ON brandlist.id = gamelist.brandname
            ORDER BY gid
         ),
    b AS (SELECT brandlist.id as bid,
                 brandlist.brandname as bname
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
    ug AS (SELECT gamelist.id as gid,
                  gamename as gname,
                  CASE WHEN dmm_genre='digital' AND dmm_genre_2='pcgame'
                        THEN 'https://pics.dmm.co.jp/digital/pcgame/' || dmm || '/' || dmm || 'pl.jpg'
                       WHEN dmm_genre='digital' AND dmm_genre_2='doujin'
                        THEN 'https://doujin-assets.dmm.co.jp/digital/game/' || dmm || '/' || dmm || 'pr.jpg'
                       WHEN dmm_genre='mono' AND dmm_genre_2='pcgame'
                        THEN 'https://pics.dmm.co.jp/mono/game/' || dmm || '/' || dmm || 'pl.jpg'
                       WHEN dlsite_id IS NOT NULL AND (dlsite_domain='pro' OR dlsite_domain='soft')
                        THEN 'https://img.dlsite.jp/modpub/images2/work/professional/' || left(dlsite_id,2) || LPAD(CAST(CAST(RIGHT(LEFT(dlsite_id, 5), 3) AS INTEGER) + 1 AS TEXT), 3, '0') || '000/' || dlsite_id || '_img_main.jpg'
                       WHEN dlsite_id IS NOT NULL
                        THEN 'https://img.dlsite.jp/modpub/images2/work/doujin/' || left(dlsite_id,2) || LPAD(CAST(CAST(RIGHT(LEFT(dlsite_id, 5), 3) AS INTEGER) + 1 AS TEXT), 3, '0') || '000/' || dlsite_id || '_img_main.jpg'
                       WHEN dmm IS NOT NULL
                        THEN 'https://pics.dmm.co.jp/mono/game/' || dmm || '/' || dmm || 'pl.jpg'
                       WHEN surugaya_1 IS NOT NULL AND surugaya_1 != 0
                        THEN 'https://www.suruga-ya.jp/database/pics/game/' || surugaya_1 || '.jpg'
                       ELSE '' END AS thumbnail_url,
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
    ub AS (SELECT bid,
                  bname,
                  array_agg(gid) as gid,
                  array_agg(gname) as gname,
                  array_agg(model) as model,
                  array_agg(possession) as possession,
                  array_agg(thumbnail_url) AS thumbnail_url
             FROM ug
             GROUP BY bid,
                      bname
             ORDER BY bid
          )

    SELECT * FROM {table}"""


def dl_dump(user, table):
    sql = SQL.format(user=user, table=table)
    response = request("https://erogamescape.dyndns.org/~ap2/ero/toukei_kaiseki/sql_for_erogamer_form.php", data={"sql": sql})
    soup = BeautifulSoup(response, features='html.parser')
    tbl = soup.find('div', attrs={'id': 'query_result_main'}).find('table')
    rows = iter(tbl)
    next(rows)
    headers = [col.text for col in next(rows)]
    return headers, rows


def get_userlist(root='.', offline=False, user=None, dump=True):
    if offline:
        try:
            logger_egs.debug('Checking for existing dumps...')
            latest_off = natsorted(filter(lambda x: regex.match(pattern_save('ub'), os.path.splitext(x)[0]) and os.path.splitext(x)[1] == '.json', next(os.walk(root))[2]))[-1]
            logger_egs.debug('Using "%s" the as latest dump.', latest_off)
        except IndexError:
            raise RuntimeError
        with open(os.path.join(root, latest_off), 'r', encoding='utf-8') as f:
            return json.load(f)
    headers, rows = dl_dump(user=user, table='ub')
    del headers[0]
    headers[0] = 'name'
    dmp = {'info': format_save('ub')}
    for row in rows:
        if row == '\n':
            continue
        values = [col.text for col in row]
        dmp[values[0]] = dict(zip(headers, values[1:]))

        agg = ['name', 'platform', 'possession', 'thumbnail']
        lsg = dmp[values[0]]['gname'][1:-1].split(',')
        j = 0
        while j < len(lsg):
            if ' ' in lsg[j] and lsg[j].startswith('"') and lsg[j].endswith('"'):
                lsg[j] = lsg[j][1:-1]
            elif ' ' in lsg[j] and lsg[j].startswith('"'):  # name was split due to ',' inside it
                lsg[j + 1] = lsg[j] + lsg[j + 1]  # add it to the next name and deal with it then
                del lsg[j]
                continue
            j += 1

        dmp[values[0]]['g'] = {id: dict(zip(agg, val))
                               for id, val in
                               zip(dmp[values[0]]['gid'][1:-1].split(','),
                               zip(lsg, # gname
                                   dmp[values[0]]['model'][1:-1].split(','),
                                   map(lambda x: True if x == 't' else False if x == 'f' else None, dmp[values[0]]['possession'][1:-1].split(',')),
                                   map(lambda x: None if x == '""' else x, dmp[values[0]]['thumbnail_url'][1:-1].split(','))
                                   ))}
        del dmp[values[0]]['gid']
        del dmp[values[0]]['gname']
        del dmp[values[0]]['model']
        del dmp[values[0]]['possession']
        del dmp[values[0]]['thumbnail_url']
    if dump:
        with open(os.path.join(root, dmp['info'] + '.json'), 'w', encoding='utf-8') as f:
            json.dump(dmp, f, ensure_ascii=False)
    return dmp
