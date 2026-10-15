#!/usr/bin/env python3
"""fetch_map.py WEBROOT SLUG  : mirror one map pack from vel.gg into WEBROOT (five -> root). Uses curl (python UA is 403'd).
Fetches live manifest + every file (plain/original and, if the entry has 'opus', the .kop too) + streams. Resumable (skips files of right size)."""
import json, os, subprocess, sys, concurrent.futures as cf
web, slug = sys.argv[1], sys.argv[2]
mdir = web if slug == 'five' else os.path.join(web, slug)
murl = 'https://vel.gg/bo1z/manifest.json' if slug == 'five' else f'https://vel.gg/bo1z/{slug}/manifest.json'
cdn = f'https://cdn.vel.gg/packs/{slug}/'
os.makedirs(mdir, exist_ok=True)
raw = subprocess.run(['curl','-sSf','-m','60',murl],capture_output=True,check=True).stdout
open(os.path.join(mdir,'manifest.json'),'wb').write(raw)
m = json.loads(raw)
jobs = []
for e in m['files'] + m.get('streams', []):
    fb = e.get('fallback')
    jobs.append((e['path'], (fb or e)['size']))
    if e.get('opus'): jobs.append((e['path'] + '.kop', e['opus']))
def get(j):
    p, size = j
    dest = os.path.join(mdir, 'pack', p); os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.isfile(dest) and os.path.getsize(dest) == size: return p, 'have'
    for _ in range(4):
        r = subprocess.run(['curl','-sSf','-m','1800','-C','-','-o',dest,cdn+p.replace(' ','%20')],capture_output=True)
        if r.returncode == 0 and os.path.getsize(dest) == size: return p, 'ok'
    return p, 'FAIL ' + r.stderr.decode()[:100]
with cf.ThreadPoolExecutor(6) as ex:
    for p, s in ex.map(get, jobs):
        if s != 'ok' and s != 'have': print(slug, p, s, flush=True)
print(slug, 'done', len(jobs), 'files', flush=True)
