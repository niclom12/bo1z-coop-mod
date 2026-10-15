#!/usr/bin/env python3
"""rawfiles.py RAW OUTDIR : extract RawFile assets (zlib-compressed script/text) from a decompressed BO1 xfile stream.
Heuristic: find each 'name\\0' string ending in .gsc/.csc/.txt/.cfg/.csv etc, parse the RawFile struct before the name block is not needed:
we scan for zlib streams that decode to text and attribute them to the nearest preceding path string."""
import sys, re, zlib, os
raw = open(sys.argv[1], 'rb').read(); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
names = [(m.start(), m.group().decode()) for m in re.finditer(rb'(?:maps|clientscripts|common_scripts|animscripts|character|mp|ui)[A-Za-z0-9_/\\\.\-]*\.(?:gsc|csc)\x00', raw)]
import bisect
pos = [p for p, _ in names]
found = 0
for m in re.finditer(rb'\x78[\x01\x9c\xda]', raw):
    s = m.start()
    try:
        o = zlib.decompressobj(); d = o.decompress(raw[s:s+2000000])
    except Exception: continue
    if len(d) < 64 or not o.eof: continue
    head = d[:4000]
    if not re.fullmatch(rb'[\x09\x0a\x0d\x20-\x7e]*', head): continue
    i = bisect.bisect_right(pos, s) - 1
    nm = names[i][1].rstrip('\x00') if i >= 0 else 'unknown'
    # the RawFile name string comes right BEFORE its data in the stream
    fn = os.path.join(out, nm.replace('\\', '/').replace('/', '__') + ('' if i>=0 else '_%d' % s))
    while os.path.exists(fn): fn += '_'
    open(fn, 'wb').write(d); found += 1
print('extracted', found)
