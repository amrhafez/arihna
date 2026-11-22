#!/usr/bin/env python3
"""Sign an Arihna announcements file (1.2.2 and later).

Usage: python3 sign.py <items.json> <out.json> --kid t1|p1
The private key (PEM, P-256) is read from the ANN_KEY environment variable, never from the repository.
The app checks the signature over the exact payload string (ECDSA P-256, SHA-256, raw r||s, base64).
"""
import base64, datetime, json, os, sys
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

src, out = sys.argv[1], sys.argv[2]
kid = sys.argv[sys.argv.index('--kid') + 1] if '--kid' in sys.argv else 'p1'
data = json.load(open(src, encoding='utf-8'))
assert data.get('v') == 1 and isinstance(data.get('items'), list), 'need {"v":1,"items":[...]}'
for it in data['items']:
    for k in ('id', 'country', 'ev', 'state', 'from'):
        assert k in it, f'item {it.get("id")} lacks {k}'
    assert it['state'] in ('expected', 'announced'), it['state']
    # 1.2.2 pipeline checks: only the countries Arihna serves, real dates, both languages where text is shown
    import re as _re
    assert it['country'] in ('ae', 'sa', 'eg', 'gb', 'us', 'ca', 'om', 'bh', 'qa', 'jo', 'kw'), it['country']
    assert _re.fullmatch(r'20\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])', str(it['ev'])), it['ev']
    datetime.datetime.fromisoformat(it['from'].replace('Z', '+00:00'))
    for k in ('lab', 'name', 'dl', 'short', 'by'):
        if k in it: assert it[k].get('en') and it[k].get('ar'), f'{it["id"]}: {k} needs en and ar'
    if 'notify' in it:
        n = it['notify']; datetime.datetime.fromisoformat(n['at'].replace('Z', '+00:00'))
        assert n['title'].get('en') and n['title'].get('ar') and n['body'].get('en') and n['body'].get('ar'), f'{it["id"]}: notify text'
# 1.3 update notice (optional): {"version": "1.4", "head": {"en","ar"}, "body": {"en","ar"}, "important": bool,
#   "countries": ["qa", ...] (important only; empty = all), "notify": {"at", "title": {..}, "body": {..}}, "testStore": "1.4" (test file only)}
u = data.get('update')
if u is not None:
    import re
    assert re.fullmatch(r'\d+(\.\d+){0,3}', u.get('version', '')), 'update.version like 1.4'
    assert isinstance(u.get('head'), dict) and u['head'].get('en') and u['head'].get('ar'), 'update.head needs en and ar'
    if u.get('important'):
        assert isinstance(u.get('body'), dict) and u['body'].get('en') and u['body'].get('ar'), 'an important update needs body en and ar'
    if 'testStore' in u:
        assert kid.startswith('t'), 'testStore is for the test file only'
# the app refuses a file issued before the last one it accepted, so every signing stamps the time
import datetime
data['issued'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
key = serialization.load_pem_private_key(os.environ['ANN_KEY'].encode(), None)
r, s = decode_dss_signature(key.sign(payload.encode('utf-8'), ec.ECDSA(hashes.SHA256())))
sig = base64.b64encode(r.to_bytes(32, 'big') + s.to_bytes(32, 'big')).decode()
json.dump({'kid': kid, 'payload': payload, 'sig': sig}, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
print(f'signed {len(data["items"])} items with {kid} -> {out}')
