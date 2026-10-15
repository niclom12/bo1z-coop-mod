#!/usr/bin/env python3
"""xsurf2.py: parse XSurface groups (contiguous 68-byte structs followed by per-surface inline data) from a decompressed BO1 xfile stream.
Library: parse(raw) -> list of surface dicts {st, vc, tc, verts (np structured), tris (tc x 3 u16), group, idx}.
Per surface after the struct array: vertsBlend (2*nb bytes), verts0 (32*vc), vertList (12*vlc, + inline collision tree when present), triIndices (6*tc).
The triIndices block is located by scanning forward for a plausible index block (all < vc), since the nested collision tree is variable length."""
import struct, numpy as np, re
VDT = np.dtype([('xyz', '<f4', 3), ('bn', '<f4'), ('col', '<u4'), ('uv', '<u4'), ('nrm', '<u4'), ('tan', '<u4')])
def groups(d):
    seen = set(); out = []
    for m in re.finditer(rb'\xff\xff\xff\xff\x00\x00\x00\x00', d):
        s = m.start() - 32
        if s < 0 or s in seen: continue
        if not ok(d, s): continue
        # walk back to the group's first struct
        while s - 68 >= 0 and ok(d, s - 68): s -= 68
        if s in seen: continue
        g = []; t = s
        while t + 68 <= len(d) and ok(d, t): g.append(t); seen.add(t); t += 68
        out.append((s, g, t))
    return out
def ok(d, s):
    if d[s + 32:s + 36] != b'\xff\xff\xff\xff' or d[s + 12:s + 16] != b'\xff\xff\xff\xff' or d[s + 36:s + 40] != b'\0\0\0\0' or d[s + 44:s + 48] != b'\0\0\0\0': return False
    tm, vlc, fl, vc, tc = struct.unpack_from('<BBHHH', d, s)
    return 3 <= vc < 20000 and 1 <= tc < 40000 and tm < 8 and vlc < 80
def parse(d):
    res = []
    for gi, (s, g, end) in enumerate(groups(d)):
        pos = end
        for k, st in enumerate(g):
            tm, vlc, fl, vc, tc = struct.unpack_from('<BBHHH', d, st); vi = struct.unpack_from('<4h', d, st + 16)
            vb, tens = struct.unpack_from('<II', d, st + 24); vl = struct.unpack_from('<I', d, st + 40)[0]
            nb = 7 * vi[3] + 5 * vi[2] + 3 * vi[1] + vi[0]
            if vb == 0xFFFFFFFF: pos += 2 * nb
            if tens == 0xFFFFFFFF: pos += 12 * (vi[3] + vi[2] + vi[1] + vi[0])  # approx; tension rare
            vp = pos
            if vp + 32 * vc > len(d): break
            verts = np.frombuffer(d, dtype=VDT, count=vc, offset=vp); pos = vp + 32 * vc
            tris = None
            if vl != 0xFFFFFFFF:
                n = 3 * tc
                if struct.unpack_from('<I', d, st + 12)[0] == 0xFFFFFFFF and pos + 2 * n <= len(d):
                    t = np.frombuffer(d, dtype='<u2', count=n, offset=pos).reshape(-1, 3)
                    if t.max() < vc: tris = t; pos += 2 * n
            else:
                q = pos + 12 * vlc
                for j in range(vlc):
                    cp = struct.unpack_from('<I', d, pos + 12 * j + 8)[0]
                    if cp == 0xFFFFFFFF:
                        nc, nptr, lc, lptr = struct.unpack_from('<IIII', d, q + 24); q += 40
                        if nptr == 0xFFFFFFFF: q += 16 * nc
                        if lptr == 0xFFFFFFFF: q += 2 * lc
                n = 3 * tc
                if struct.unpack_from('<I', d, st + 12)[0] == 0xFFFFFFFF and q + 2 * n <= len(d):
                    t = np.frombuffer(d, dtype='<u2', count=n, offset=q).reshape(-1, 3)
                    if t.max() < vc: tris = t; pos = q + 2 * n
            res.append(dict(st=st, vp=vp, vc=vc, tc=tc, verts=verts, tris=tris, group=gi, idx=k, tm=tm, vlc=vlc))
            if tris is None: break
    return res
def uv(v): return v['uv'].copy().view('<u2').reshape(-1, 2).view('<f2').astype(np.float32)
if __name__ == '__main__':
    import sys
    d = open(sys.argv[1], 'rb').read(); S = parse(d); print(len(S), 'surfaces', sum(1 for s in S if s['tris'] is not None), 'with tris')
