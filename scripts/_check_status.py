import json
from collections import Counter

with open('data/rag_storage/kv_store_doc_status.json', encoding='utf-8') as f:
    d = json.load(f)

print('total:', len(d))
print(Counter(v.get('status') for v in d.values()))
print()
for k, v in d.items():
    if v.get('status') != 'processed':
        print('---')
        print('id:', k)
        for kk, vv in v.items():
            if kk == 'content':
                print(f'{kk}: <{len(vv)} chars>')
                print('--- content head ---')
                print(vv[:600])
                print('--- content tail ---')
                print(vv[-400:])
            else:
                s = str(vv)
                print(f'{kk}: {s[:600]}')
