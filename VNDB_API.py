import json
from datetime import datetime
from os.path import join

import regex
import requests
from natsort import natsorted

import helper

status = ['Unknown', 'Pending', 'Obtained', 'On loan', 'Deleted']
save_format = 'VNDB{full_backup}-{date}'
regex_pattern = r'$VNDB{full_backup}-\d{4}(-\d\d){2}T\d{6}Z\.json^'


def dump(user, full_backup):
    if full_backup:
        req = {
            "fields": "id, labels.label, started, finished, notes, vn{title, alttitle, image{id, url}}, releases{list_status, id, title, alttitle, platforms, vns.id, patch, released, notes}"
        }
    else:
        req = {
            "fields": "id, labels.label, vn{title, alttitle, image{id, url}}, releases{list_status, id, title, alttitle, platforms, vns.id, patch}"
        }
    req['user'] = user
    req['results'] = 100
    i = 0
    dmp = [save_format.format(full_backup='-full_backup' if full_backup else '',
                              date=datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ"))]
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
                r['status'] = status[r['list_status']]
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
    return filter(
        lambda x: regex.match(regex_pattern.replace('{full_backup}', '-full_backup' if full_backup else ''),
                              x) is not None,
        natsorted(next(helper.walklevel(root))[2]))


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


def main():
    user = None
    if user is None:
        user = helper.ask('user:')
    full_backup = bool(input('Dump entire userlist? Empty for N anything for Y\n>'))
    write_dump(full_backup, user=user)


if __name__ == '__main__':
    main()
