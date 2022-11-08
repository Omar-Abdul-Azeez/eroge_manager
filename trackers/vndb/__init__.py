# -*- encoding:utf-8 -*-
import json
from datetime import datetime
from os.path import join

import regex
import requests
from natsort import natsorted

from ... import helper

__STATUS = ['Unknown', 'Pending', 'Obtained', 'On loan', 'Deleted']
__DATE_FORMAT = '%Y-%m-%dT%H%M%SZ'
__SAVE_FORMAT = 'VNDB{full_backup}-{date}'
__REGEX_PATTERN = r'$VNDB{full_backup}-\d{4}(-\d\d){2}T\d{6}Z\.json^'
__REQ_FULL = {"fields": "id,"
                        "labels.label,"
                        "started,"
                        "finished,"
                        "notes,"
                        "vn{title, alttitle, image{id, url}},"
                        "releases{list_status, id, title, alttitle, platforms, vns.id, patch, released, notes}"}
__REQ_NORM = {"fields": "id,"
                        "labels.label,"
                        "vn{title, alttitle, image{id, url}},"
                        "releases{list_status, id, title, alttitle, platforms, vns.id, patch}"}


def dump(user, full_backup):
    if full_backup:
        req = __REQ_FULL.copy()
    else:
        req = __REQ_NORM.copy()
    req['user'] = user
    req['results'] = 100
    i = 0
    dmp = [__SAVE_FORMAT.format(full_backup='-full_backup' if full_backup else '',
                                date=datetime.utcnow().strftime(__DATE_FORMAT))]
    while True:
        i += 1
        req['page'] = i
        res = requests.post("https://api.vndb.org/kana/ulist", json=req)
        res = res.json()
        for vn in res['results']:
            lbls = []
            for lbl in vn['labels']:
                lbls.append(lbl['label'])
            vn['labels'] = lbls
            title = ''
            if vn['vn']['alttitle'] == '':
                title = vn['vn']['title']
            else:
                title = vn['vn']['alttitle']
            vn['cover'] = vn['vn']['image']
            vn['name'] = title
            del vn['vn']
            for r in vn['releases']:
                r['status'] = __STATUS[r['list_status']]
                del r['list_status']
                if r['alttitle'] == '':
                    title = r['title']
                else:
                    title = r['alttitle']
                r['name'] = title
                del r['title']
                del r['alttitle']
                vns = []
                for v in r['vns']:
                    vns.append(v['id'])
                r['vns'] = vns
            dmp.append(vn)
        if not res['more']:
            break
    return dmp


def write_dump(user=None, full_backup=None, dmp=None, root='.'):
    if dmp is None:
        if user is None or full_backup is None:
            raise ValueError
        dmp = dump(user, full_backup)
    with open(join(root, dmp[0] + '.json'), 'w', encoding='utf-8') as f:
        json.dump(dmp, f, ensure_ascii=False)


def local_dumps(full_backup, root='.'):
    return natsorted(filter(lambda x: regex.match(__REGEX_PATTERN.replace('{full_backup}', '-full_backup' if full_backup else ''), x) is not None,
                            next(helper.walklevel(root))[2]))


def get_dump(full_backup, root='.', can_dl=False, user=None, none=False):
    ls = list(local_dumps(full_backup, root=root))
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
            return dump(user, full_backup)
        else:
            with open(ans, 'r', encoding='utf-8') as f:
                return json.load(f)
