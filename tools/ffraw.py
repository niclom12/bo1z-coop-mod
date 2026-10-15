#!/usr/bin/env python3
"""ffraw.py IN.ff OUT.bin : decompress a BO1 fastfile (IWffu100 = 12-byte header + zlib stream; IWffr100 = 48-byte header + raw stream) to the raw xfile stream."""
import sys, zlib
d = open(sys.argv[1], 'rb').read()
m = d[:8]
if m == b'IWffu100':
    o = zlib.decompressobj(); out = o.decompress(d[12:])
elif m == b'IWffr100':
    out = d[48:]
else:
    sys.exit('unknown magic %r' % m)
open(sys.argv[2], 'wb').write(out); print(m, len(d), '->', len(out))
