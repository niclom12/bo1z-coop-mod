#!/usr/bin/env python3
"""preview_heads.py ZT_RAW IWI OUT.png : offline renders (front / 3-4 view) of every head mesh found by bake_face.find_heads, textured with an IWi (u,v direct)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import xsurf2, numpy as np, render_mesh, iwilib, bake_face
from PIL import Image
zt, iwi, out = sys.argv[1:4]
SS = {'zt': xsurf2.parse(open(zt, 'rb').read())}; tex = iwilib.to_image(iwi)
H = bake_face.find_heads(SS['zt']); W = Image.new('RGB', (len(H) * 260, 520))
for k, (src, i, fk, eyes) in enumerate(H):
    s = SS[src][i]; xyz = s['verts']['xyz'].astype(float); uv = xsurf2.uv(s['verts']).astype(float); fr = bake_face.FR[fk]
    f = np.zeros(3); f[fr['front']] = 1; up = np.zeros(3); up[fr['up']] = 1; side = f + 0.8 * np.cross(up, f)
    W.paste(render_mesh.render(xyz, uv, s['tris'], tex, f, up=up, size=260), (k * 260, 0)); W.paste(render_mesh.render(xyz, uv, s['tris'], tex, side, up=up, size=260), (k * 260, 260))
W.save(out)
