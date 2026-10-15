#!/usr/bin/env python3
"""ksp.py: read / rebuild the web build's sounds.pack (KSPK container + KSIX path index) and swap loaded-sound clips.
Usage:
  ksp.py list  PACK [REGEX]                       list KSIX entries (alias file path -> clip, frames, bytes)
  ksp.py roundtrip PACK                           rebuild unchanged and compare bytes
  ksp.py swap  PACK OUT --map REGEX=WAV [--map ...] [--keep-frames]
        for every KSIX entry whose game path matches REGEX (case-insens., backslash paths), replace its clip with WAV
        (PCM16 mono wav, same rate as the engine expects, 44100 for zombie vox). Updates record + KSIX (frames, sha).
Format (derived from download-worker.js fetchOpus + inspection, 2026-10-13):
  KSPK: 'KSPK' u32 ver=1 u32 count u32 headLen u32 totalSize u32 0 ; then count records
        {u32 off,u32 len,u32 fmt,u32 nameLen,sha256[32],name} (fmt 0 = sounds.bin, 1 = clips/*.wav); data follows contiguously.
  sounds.bin (KSIX): 'KSIX' u32 ver=1 u32 count ; entries {u32 pathLen,u32 clipLen,u32 frames,sha256[32],path,clip}."""
import sys, struct, hashlib, re, io

def rd(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'KSPK', 'not a KSPK'
    ver, n, headLen, total, z = struct.unpack('<5I', d[4:24])
    o = 24; recs = []
    for _ in range(n):
        off, ln, fmt, nl = struct.unpack('<4I', d[o:o+16]); sha = d[o+16:o+48]; name = d[o+48:o+48+nl].decode('latin1')
        recs.append([name, fmt, d[off:off+ln], sha]); o += 48 + nl
    assert o == 24 + headLen, (o, headLen)
    return ver, recs

def wr(ver, recs):
    head = bytearray(); data = bytearray(); n = len(recs)
    hl = sum(48 + len(r[0]) for r in recs); base = 24 + hl
    for name, fmt, blob, sha in recs:
        head += struct.pack('<4I', base + len(data), len(blob), fmt, len(name)) + sha + name.encode('latin1'); data += blob
    return b'KSPK' + struct.pack('<5I', ver, n, hl, base + len(data), 0) + bytes(head) + bytes(data)

def ksix_rd(b):
    assert b[:4] == b'KSIX'; ver, n = struct.unpack('<2I', b[4:12]); pos = 12; ents = []
    for _ in range(n):
        pl, cl, fr = struct.unpack('<3I', b[pos:pos+12]); sha = b[pos+12:pos+44]
        path = b[pos+44:pos+44+pl].decode('latin1'); clip = b[pos+44+pl:pos+44+pl+cl].decode('latin1'); ents.append([path, clip, fr, sha]); pos += 44 + pl + cl
    assert pos == len(b)
    return ver, ents

def ksix_wr(ver, ents):
    out = bytearray(b'KSIX' + struct.pack('<2I', ver, len(ents)))
    for path, clip, fr, sha in ents:
        out += struct.pack('<3I', len(path), len(clip), fr) + sha + path.encode('latin1') + clip.encode('latin1')
    return bytes(out)

def load(path):
    ver, recs = rd(path); idx = [r for r in recs if r[1] == 0][0]
    kver, ents = ksix_rd(idx[2]); return ver, recs, idx, kver, ents

def wav_info(b):
    assert b[:4] == b'RIFF' and b[8:12] == b'WAVE'
    p = 12; fmt = None; dlen = None
    while p + 8 <= len(b):
        cid = b[p:p+4]; sz = struct.unpack('<I', b[p+4:p+8])[0]
        if cid == b'fmt ': fmt = struct.unpack('<HHIIHH', b[p+8:p+24])
        if cid == b'data': dlen = sz
        p += 8 + sz + (sz & 1)
    tag, ch, rate, bps, blk, bits = fmt
    return tag, ch, rate, bits, (dlen // blk if tag == 1 else None)

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    cmd = a[0]
    if cmd == 'list':
        ver, recs, idx, kver, ents = load(a[1]); rx = re.compile(a[2] if len(a) > 2 else '.', re.I); byname = {r[0]: r for r in recs}
        for path, clip, fr, sha in ents:
            if rx.search(path): print(f'{fr:8d} {len(byname[clip][2]):8d} {path}')
    elif cmd == 'roundtrip':
        ver, recs, idx, kver, ents = load(a[1]); idx[2] = ksix_wr(kver, ents)
        out = wr(ver, recs); print('identical' if out == open(a[1], 'rb').read() else 'DIFFERENT')
    elif cmd == 'swap':
        src, dst = a[1], a[2]; maps = []; i = 3
        while i < len(a):
            if a[i] == '--map': k, v = a[i+1].rsplit('=', 1); maps.append((re.compile(k, re.I), v)); i += 2
            else: i += 1
        ver, recs, idx, kver, ents = load(src); byname = {r[0]: r for r in recs}; used = {}; changed = 0
        for e in ents:
            for rx, wavp in maps:
                if not rx.search(e[0]): continue
                w = open(wavp, 'rb').read(); tag, ch, rate, bits, frames = wav_info(w); assert tag == 1 and bits == 16 and ch == 1, 'need PCM16 mono wav'
                sh = hashlib.sha256(w).digest(); nm = 'clips/' + sh.hex() + '.wav'
                if nm not in byname: r = [nm, 1, w, sh]; recs.append(r); byname[nm] = r
                e[1] = nm; e[2] = frames; e[3] = sh; changed += 1; break
        refs = {e[1] for e in ents}; recs[:] = [r for r in recs if r[1] == 0 or r[0] in refs]
        idx[2] = ksix_wr(kver, ents); idx[3] = hashlib.sha256(idx[2]).digest()
        open(dst, 'wb').write(wr(ver, recs)); print('swapped', changed, 'entries; records', len(recs))
if __name__ == '__main__': main()
