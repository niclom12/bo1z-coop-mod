#!/usr/bin/env python3
"""mkmod.py SITE MAPDIR [--file REL=LOCAL]... [--replace REL=LOCAL]...
Adds loose mod files to a map pack and rewrites that map's manifest.json so the browser downloader fetches them.
  --file REL=LOCAL     add/overwrite pack/REL (REL like mods/<name>/maps/... or mods/<name>/images/x.iwi); kind 'mod'
  --replace REL=LOCAL  replace an existing pack file (e.g. web/sound/sounds.pack): drops opus/fallback/br/local_parts so
                       the plain file (new size + sha256) is what the downloader fetches
SITE/MAPDIR may be a symlink farm (tools/dev/mk_testsite.sh): symlinks are removed before writing, targets never touched.
MAPDIR is '.' for the root map (Five). Recomputes total_bytes, class_bytes and a new manifest version."""
import sys, os, json, hashlib, shutil
site, mapdir = sys.argv[1], sys.argv[2]
adds, reps, i = [], [], 3
while i < len(sys.argv):
    k = sys.argv[i]; rel, loc = sys.argv[i+1].split('=', 1)
    (adds if k == '--file' else reps).append((rel, loc)); i += 2
mroot = os.path.normpath(os.path.join(site, mapdir)); mp = os.path.join(mroot, 'manifest.json')
m = json.load(open(mp)); files = m['files']; by = {f['path']: f for f in files}
def put(rel, loc):
    dst = os.path.join(mroot, 'pack', rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.islink(dst) or os.path.exists(dst): os.unlink(dst)
    shutil.copyfile(loc, dst); b = open(dst, 'rb').read(); return len(b), hashlib.sha256(b).hexdigest()
for rel, loc in adds:
    size, sha = put(rel, loc)
    e = by.get(rel) or {'path': rel, 'kind': 'mod', 'priority': 'boot', 'class': 'boot'}
    for k in ('br', 'opus', 'fallback', 'local_parts', 'dxs'): e.pop(k, None)
    e.update(size=size, sha256=sha)
    if rel not in by: files.append(e); by[rel] = e
for rel, loc in reps:
    e = by[rel]; size, sha = put(rel, loc)
    for k in ('br', 'opus', 'fallback', 'local_parts', 'dxs'): e.pop(k, None)
    e.update(size=size, sha256=sha)
    ko = os.path.join(mroot, 'pack', rel + '.kop')   # stale opus container no longer matches
    if os.path.lexists(ko): os.unlink(ko)
m['total_bytes'] = sum(f['size'] for f in files)
cb = {c: 0 for c in m['classes']}
for f in files: cb[f['class']] = cb.get(f['class'], 0) + f['size']
m['class_bytes'] = cb
m['version'] = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
if os.path.islink(mp): os.unlink(mp)
json.dump(m, open(mp, 'w'), indent=1)
print('manifest', mp, 'files', len(files), 'version', m['version'][:12])
