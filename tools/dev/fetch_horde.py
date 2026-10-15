#!/usr/bin/env python3
"""fetch_horde.py WEBROOT SLUG: fetch pack/web-manifest-horde.json (Hell mode overlay) and the files whose sha differs from the base manifest."""
import json, os, subprocess, sys
web, slug = sys.argv[1], sys.argv[2]
mdir = web if slug == 'five' else os.path.join(web, slug)
base = f'https://vel.gg/bo1z/' + ('' if slug == 'five' else slug + '/') + 'pack/'
cdn = f'https://cdn.vel.gg/packs/{slug}/'
raw = subprocess.run(['curl','-sSf','-m','60',base+'web-manifest-horde.json'],capture_output=True,check=True).stdout
os.makedirs(os.path.join(mdir,'pack','web'),exist_ok=True)
open(os.path.join(mdir,'pack','web-manifest-horde.json'),'wb').write(raw)
h=json.loads(raw); b={f['path']:f for f in json.load(open(os.path.join(mdir,'manifest.json')))['files']}
n=0
for e in h['files']:
    if e['path'] in b and b[e['path']]['sha256']==e['sha256']: continue
    fb=e.get('fallback'); jobs=[(e['path'],(fb or e)['size'])]+([(e['path']+'.kop',e['opus'])] if e.get('opus') else [])
    for p,size in jobs:
        dest=os.path.join(mdir,'pack',p); os.makedirs(os.path.dirname(dest),exist_ok=True)
        if os.path.isfile(dest) and os.path.getsize(dest)==size: continue
        subprocess.run(['curl','-sSf','-m','1800','-o',dest,cdn+p],check=True); n+=1
        print(slug,'fetched',p,os.path.getsize(dest),size)
print(slug,'horde ok, new files',n)
