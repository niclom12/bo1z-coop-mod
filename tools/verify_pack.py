#!/usr/bin/env python3
"""verify_pack.py SITE_ROOT MAPDIR [--hash]  (MAPDIR '.' for root map).
Checks each manifest entry: plain file (fallback size/sha if entry has 'fallback', else entry size/sha; text 'loose'
files compared after LF->CRLF) and/or the .kop opus container (size=entry.opus, sha=entry.sha256). Files may be a
directory <path>.part/<k> of 8 MiB chunks. An entry is OK if either plain or kop form verifies."""
import json, os, sys, hashlib
root, mapdir = sys.argv[1], sys.argv[2]; dohash = '--hash' in sys.argv
mroot = os.path.normpath(os.path.join(root, mapdir))
m = json.load(open(os.path.join(mroot, 'manifest.json')))
pack = os.path.join(mroot, 'pack')
def chunks(p):
    if os.path.isfile(p): return [p]
    if os.path.isdir(p + '.part'): return [os.path.join(p + '.part', k) for k in sorted(os.listdir(p + '.part'), key=int)]
    return []
def check(p, size, sha, crlf=False):
    cs = chunks(p)
    if not cs: return 'missing'
    if crlf and len(cs)==1:
        d = open(cs[0],'rb').read().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
        return 'ok' if (len(d)==size and hashlib.sha256(d).hexdigest()==sha) else 'bad(crlf)'
    tot = sum(os.path.getsize(c) for c in cs)
    if tot != size: return f'size {tot}!={size}'
    if dohash:
        h = hashlib.sha256()
        for c in cs:
            with open(c,'rb') as f:
                for b in iter(lambda: f.read(1<<22), b''): h.update(b)
        if h.hexdigest() != sha: return 'sha'
    return 'ok'
bad=[]; n=0; viakop=0
for e in m['files'] + m.get('streams', []):
    n+=1; res=[]
    fb = e.get('fallback')
    plain = check(os.path.join(pack,e['path']), (fb or e)['size'], (fb or e)['sha256'], crlf=(e['kind']=='loose'))
    if plain!='ok' and plain.startswith('bad(crlf)'): plain=check(os.path.join(pack,e['path']), e['size'], e['sha256'])
    res.append('plain:'+plain)
    if e.get('opus'):
        kop = check(os.path.join(pack,e['path']+'.kop'), e['opus'], e['sha256']); res.append('kop:'+kop)
        if kop=='ok': viakop+=1
        if plain=='ok' or kop=='ok': continue
    elif plain=='ok': continue
    bad.append((e['path'], e['size'], res))
print(mapdir, m['map'], 'entries', n, 'unusable', len(bad), '(hash)' if dohash else '(size only)')
for b in bad: print('  ', *b)
sys.exit(1 if bad else 0)
