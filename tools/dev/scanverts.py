#!/usr/bin/env python3
"""scanverts.py RAW [minverts] : find runs of GfxPackedVertex-like 32-byte records (binormalSign +-1.0 at +12) in a decompressed xfile stream
and print offset, count, xyz bbox, uv bbox (half floats). Used to locate xmodel surfaces without a full zone parser."""
import sys, numpy as np
d = open(sys.argv[1], 'rb').read(); mn = int(sys.argv[2]) if len(sys.argv) > 2 else 150
a = np.frombuffer(d, dtype=np.uint8)
n = len(d)
res = []
for phase in range(4):
    m = (len(d) - phase) // 32
    w = np.frombuffer(d, dtype='<u4', count=m * 8, offset=phase).reshape(m, 8)
    ok = ((w[:, 3] == 0x3F800000) | (w[:, 3] == 0xBF800000))
    f = w[:, :3].view('<f4'); ok &= np.isfinite(f).all(1) & (np.abs(f) < 200).all(1)
    i = 0; idx = np.flatnonzero(ok)
    if not len(idx): continue
    br = np.flatnonzero(np.diff(idx) != 1) + 1; starts = np.concatenate([[0], br]); ends = np.concatenate([br, [len(idx)]])
    for s, e in zip(starts, ends):
        if e - s >= mn:
            r0, r1 = idx[s], idx[e - 1] + 1; seg = w[r0:r1]; xyz = seg[:, :3].view('<f4'); uv = seg[:, 5].copy().view('<u2').reshape(-1, 2).view('<f2').astype(np.float32)
            res.append((phase + r0 * 32, r1 - r0, xyz.min(0).round(2), xyz.max(0).round(2), uv.min(0).round(3), uv.max(0).round(3)))
for r in sorted(res): print(*r)
