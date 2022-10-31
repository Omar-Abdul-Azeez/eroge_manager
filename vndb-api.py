from datetime import date
import requests
import json
dump = bool(input('Dump entire userlist?\n>'))
if dump:
    enm = ['Unknown', 'Pending', 'Obtained', 'On loan', 'Deleted']
    req = {
        "user": "u192153",
        "fields": "id, labels.label, started, finished, notes, vn{title, alttitle, image{id, url}}, releases{list_status, id, title, alttitle, languages.lang, platforms, vns.id, patch, released, notes}",
        "results": 100
    }
else:
    req = {
    "user": "u192153",
    "filters": ["or", ["label", "=", "10"], ["label", "=", "11"], ["label", "=", "13"]],
    "fields": "id, vn{title, alttitle, image{id, url}}, releases{list_status, id, title, alttitle, platforms, vns.id, patch}",
    "results": 100
    }
i = 0
try:
    with open(f'vndb-{date.today().strftime("%Y-%m-%d")}.json', 'w', encoding='utf-8') as f:
        f.write('[')
        while True:
            i += 1
            req['page'] = i
            r = requests.post("https://api.vndb.org/kana/ulist", json=req)
            r = r.json()
            for vn in r['results']:
                if dump:
                    lbls = []
                    for lbl in vn['labels']:
                        lbls.append(lbl['label'])
                    vn['labels'] = lbls
                title = ''
                if vn['vn']['alttitle'] == '':
                    title = vn['vn']['title']
                else:
                    title = vn['vn']['alttitle']
                img = vn['vn']['image']
                del vn['vn']
                vn['title'] = title
                vn['cover'] = img
                ind = 0
                while ind < len(vn['releases']):
                    if vn['releases'][ind]['list_status'] != 2 and not dump:
                        del vn['releases'][ind]
                    else:
                        if dump:
                            langs = []
                            for lang in vn['releases'][ind]['languages']:
                                langs.append(lang['lang'])
                            vn['releases'][ind]['languages'] = langs
                            vn['releases'][ind]['status'] = enm[vn['releases'][ind]['list_status']]
                        del vn['releases'][ind]['list_status']
                        if vn['releases'][ind]['alttitle'] == '':
                            del vn['releases'][ind]['alttitle']
                        else:
                            vn['releases'][ind]['title'] = vn['releases'][ind]['alttitle']
                            del vn['releases'][ind]['alttitle']
                        vns = []
                        for v in vn['releases'][ind]['vns']:
                            vns.append(v['id'])
                        vn['releases'][ind]['vns'] = vns
                        ind += 1
            if i != 1:
                f.write(', ')
            f.write(json.dumps(r['results'], ensure_ascii=False)[1:-1])
            f.flush()
            if r['more'] == False:
                break
        f.write(']')
except Exception as e:
    print(f"page: {i} error")
    print(e)
    input()