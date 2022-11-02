# -*- encoding:utf-8 -*-
import json
from datetime import date

import requests
from bs4 import BeautifulSoup


def dump(sql_table):
    sql = """WITH
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
                WHERE uid = 'Karasaru'
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
    
    /*
    gb = game + brand
    bg = brand + array_agg(game)
    u = userlist(gid + possession)だけ
    ugb = userlistの game + brand
    ubg = userlistの brand + array_agg(game)
    ugrgb = userlistの group + array_agg(game) + array_agg(brand)
    kankei = kankei WHERE kind IN ('apend','bundling')
    ugbkankei = userlistの game + brand + array_agg(bundle_of) + array_agg(append_to) + array_agg(bundled_in) + array_agg(appends)
    */
    """

    sql += f'SELECT * FROM {sql_table}'  # refer to the above list of tables

    r = requests.post("https://erogamescape.dyndns.org/~ap2/ero/toukei_kaiseki/sql_for_erogamer_form.php",
                      data={"sql": sql})

    soup = BeautifulSoup(r.content, features='html.parser')
    table = soup.find('div', attrs={'id': 'query_result_main'}).find('table')
    rows = iter(table)
    next(rows)
    headers = [col.text for col in next(rows)][1:]
    dmp = dict()
    for row in rows:
        if row == '\n':
            continue
        values = [col.text for col in row]
        dmp[values[0]] = dict(zip(headers, values[1:]))
        if sql_table in ['bg', 'ubg', 'ugrgb', 'ugbkankei']:
            try:
                s = dmp[values[0]]['possession']
                if s[0] == '{' and s[-1] == '}':
                    dmp[values[0]]['possession'] = list(map(lambda x: True if x == 't' else False if x == 'f' else None, s[1:-1].split(',')))
            except Exception as e:
                pass
            for agg_col in ['gid','vid','gname','model','bid','bname','bundled_in','bundle_of','appends','append_to']:
                try:
                    s = dmp[values[0]][agg_col]
                    if s[0] == '{' and s[-1] == '}':
                        tmp = s[1:-1].split(',')
                        for z in range(len(tmp)):
                            if ' ' in tmp[z] and tmp[z][0] == '"' and tmp[z][-1] == '"':
                                tmp[z] = tmp[z][1:-1]
                            if tmp[z] == 'NULL':
                                tmp[z] = None
                        dmp[values[0]][agg_col] = tmp
                except Exception as e:
                    pass
    return dmp


def write_dump(sql_table, dmp=None):
    if dmp is None:
        dmp = dump(sql_table)
    with open(f'egs-{sql_table}-{date.today().strftime("%Y-%m-%d")}.json', 'w', encoding='utf-8') as f:
        json.dump(dmp, f, ensure_ascii=False)


def main():
    def ask_sql_table():
        print("u = userlist(gid + possession)だけ\n"
              "gb = game + brand\n"
              "ugb = userlistの game + brand\n"
              "bg = brand + array_agg(game)\n"
              "ubg = userlistの brand + array_agg(game)\n"
              "ugrgb = userlistの group + array_agg(game) + array_agg(brand)\n"
              "kankei = kankei WHERE kind IN ('apend','bundling')\n"
              "ugbkankei = userlistの game + brand + array_agg(bundle_of) + array_agg(append_to) + array_agg(bundled_in) + array_agg(appends))")
        return input('SQL Table:\n>')

    sql_tables = ['u', 'gb', 'ugb', 'bg', 'ubg', 'ugrgb', 'kankei', 'ugbkankei']
    sql_table = ask_sql_table()
    while sql_table not in sql_tables:
        print()
        sql_table = ask_sql_table()
    write_dump(sql_table)


if __name__ == '__main__':
    main()
