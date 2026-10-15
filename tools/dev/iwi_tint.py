#!/usr/bin/env python3
"""iwi_tint.py IN.iwi OUT.iwi MODE : proof-of-concept recolour of a DXT1 IWi (all mips) by permuting endpoint channels. MODE: rb | rg | gb
Keeps each block's 4-colour/3-colour mode (swaps endpoints + remaps indices when the order flips)."""
import sys, struct
d = bytearray(open(sys.argv[1], 'rb').read()); mode = sys.argv[3]
assert d[:3] == b'IWi' and d[4] == 0x0B, 'DXT1 IWi only'
def tint(c):
    r, g, b = (c >> 11) & 31, (c >> 5) & 63, c & 31
    r8, g8, b8 = r*255//31, g*255//63, b*255//31
    nr, ng, nb = {'rb': (b8, g8, r8), 'rg': (g8, r8, b8), 'gb': (r8, b8, g8)}[mode]
    return ((nr*31//255) << 11) | ((ng*63//255) << 5) | (nb*31//255)
swaps = 0
for o in range(48, len(d) - 7, 8):
    c0, c1, idx = struct.unpack('<HHI', d[o:o+8]); n0, n1 = tint(c0), tint(c1)
    if (n0 > n1) != (c0 > c1):
        n0, n1 = n1, n0; swaps += 1; new = 0
        for p in range(16):
            s = (idx >> (2*p)) & 3; s = 1 - s if s < 2 else (5 - s if c0 > c1 else s); new |= s << (2*p)
        idx = new
    d[o:o+8] = struct.pack('<HHI', n0, n1, idx)
open(sys.argv[2], 'wb').write(d); print('tinted; endpoint pairs swapped:', swaps)
