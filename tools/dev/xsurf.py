#!/usr/bin/env python3
"""xsurf.py: locate XSurface records (68-byte struct + inline vertsBlend/verts0/vertList/triIndices) in a decompressed xfile stream.
Library: surfaces(raw) -> list of dict(off, vc, tc, verts(np structured), tris(Nx3 u16), nblend). Heuristic walker, validated by struct/verts adjacency."""
import struct, numpy as np
def runs(d, mn=20):
    out = []
    for phase in range(4):
        m = (len(d) - phase) // 32
        w = np.frombuffer(d, dtype='<u4', count=m * 8, offset=phase).reshape(m, 8)
        ok = ((w[:, 3] == 0x3F800000) | (w[:, 3] == 0xBF800000)); f = w[:, :3].view('<f4'); ok &= np.isfinite(f).all(1) & (np.abs(f) < 400).all(1)
        idx = np.flatnonzero(ok)
        if not len(idx): continue
        br = np.flatnonzero(np.diff(idx) != 1) + 1; st = np.concatenate([[0], br]); en = np.concatenate([br, [len(idx)]])
        for s, e in zip(st, en):
            if e - s >= mn: out.append((phase + idx[s] * 32, e - s))
    return sorted(out)
def surfaces(d, mn=20):
    res = []
    for p, c in runs(d, mn):
        # the run may start a few verts early/late; try exact struct match with vertCount==c' for c' in c..c-8
        found = None
        for cc in range(c, max(mn, c - 40), -1):
            for pp in range(p, p + 32 * (c - cc) + 1, 32):
                for s in range(pp - 68 - 2 * 4000, pp - 67):
                    if s < 0: break
                    if d[s + 32:s + 36] != b'\xff\xff\xff\xff' or d[s + 36:s + 40] != b'\0\0\0\0': continue
                    vcnt = struct.unpack_from('<H', d, s + 4)[0]
                    if vcnt != cc: continue
                    vi = struct.unpack_from('<4h', d, s + 16); nb = 7 * vi[3] + 5 * vi[2] + 3 * vi[1] + vi[0]
                    if s + 68 + 2 * nb == pp: found = (s, pp, cc, nb); break
                if found: break
            if found: break
        if not found: continue
        s, pp, cc, nb = found
        tc = struct.unpack_from('<H', d, s + 6)[0]; vlc = d[s + 1]; vl_ptr = struct.unpack_from('<I', d, s + 40)[0]; tri_ptr = struct.unpack_from('<I', d, s + 12)[0]
        vend = pp + 32 * cc
        verts = np.frombuffer(d, dtype=np.dtype([('xyz', '<f4', 3), ('bn', '<f4'), ('nrm', '<u4'), ('uv', '<u4'), ('tan', '<u4')]), count=cc, offset=pp)
        res.append(dict(off=s, voff=pp, vc=cc, tc=tc, vlc=vlc, verts=verts, vend=vend, tri_ptr=tri_ptr, vl_ptr=vl_ptr, flags=struct.unpack_from('<H', d, s + 2)[0]))
    return res
def uvs(verts): return verts['uv'].copy().view('<u2').reshape(-1, 2).view('<f2').astype(np.float32)
def find_tris(d, sf):
    """triIndices: 3*tc u16 inline after vertList(+collision data). Scan forward from vend for the first position where all 3*tc u16 < vc and form valid tris."""
    vc, tc, vend = sf['vc'], sf['tc'], sf['vend']; n = 3 * tc
    for q in range(vend, vend + 12 * 64 + 20000, 2):
        a = np.frombuffer(d, dtype='<u2', count=n, offset=q) if q + 2 * n <= len(d) else None
        if a is None: break
        if a.max() < vc and (a[0::3] != a[1::3]).all() and (a[1::3] != a[2::3]).all(): return a.reshape(-1, 3), q
    return None, None
if __name__ == '__main__':
    import sys
    d = open(sys.argv[1], 'rb').read(); S = surfaces(d, int(sys.argv[2]) if len(sys.argv) > 2 else 50)
    print(len(S), 'surfaces')
    for s in S:
        t, q = find_tris(d, s); u = uvs(s['verts']); print(s['off'], 'vc', s['vc'], 'tc', s['tc'], 'tris@', q, 'uv', u.min(0).round(2), u.max(0).round(2))
