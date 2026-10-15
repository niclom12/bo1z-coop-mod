#!/usr/bin/env python3
"""bake_face.py (fixed 2026-10-14): bake a face photo onto the 4 head strips of c_ger_zombie_head1_c. NOTE mesh UVs are transposed: texel x = uv[1]*W, y = uv[0]*H. Heads: zt 86,1185,1194,1202 only (patch.raw surfaces and zt 243 are not head1_c heads). Soft elliptical mask in photo space.
Usage: bake_face.py ZT_RAW ORIG.iwi FACE.png OUT.iwi [--preview PREFIX]
ZT_RAW: the decompressed zombie_theater.ff xfile stream (tools/ffraw.py; its 8 MiB .part/N chunks must be joined in NUMERIC order). Head meshes are read with xsurf2
and found by their signature (find_heads): a large surface directly followed by a small eyeball surface whose UVs sit in the atlas' eye patch.
Texture convention (verified in the real game, docs/MODDING.md): IWi stores the SMALLEST mip first; UV (u,v) samples the decoded image at x=u*W, y=v*H.
Mesh frames: type A (head-local models): front=+y, up=+x, lateral=+z.  type B (heads inside the body-space character models): front=+x, up=+z, lateral=+y.
The photo's pupils are anchored on the eyeball surfaces of each group; scale = pupil distance. Only front-facing triangles are painted (alpha by the front
component of the normal); every other texel (hands, back/side of heads, gibs, hair islands) is left untouched. Output keeps the template header, size, DXT1 and mip chain."""
import sys, numpy as np
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xsurf2, iwilib
from PIL import Image
# A head entry is (raw 'zt', head surface index, frame 'A'|'B', eye surface indices). The indices depend on the exact zone file, so find_heads() looks them up.
def find_heads(S, min_verts=800):
    """The head1 variants are the big surfaces (>= min_verts vertices) directly followed by an eyeball surface whose UV box is the atlas' eye patch (u .137-.2, v .703-.77).
    In the Kino zone file that gives 4 heads (the first at surface 86)."""
    out = []
    for i in range(len(S) - 1):
        if S[i]['vc'] < min_verts: continue
        uv = xsurf2.uv(S[i + 1]['verts'])
        if not uv.size: continue
        mn, mx = uv.min(0), uv.max(0)
        if abs(mn[0] - 0.137) < 0.01 and abs(mn[1] - 0.703) < 0.01 and abs(mx[0] - 0.2) < 0.015 and abs(mx[1] - 0.77) < 0.015: out.append(('zt', i, 'A', [i + 1]))
    return out
FR = {'A': dict(front=1, up=0, lat=2), 'B': dict(front=0, up=2, lat=1)}
PUPILS = ((365.0, 440.0), (655.0, 440.0))     # face_texture_front.png pupil centres (1024x1024), measured on the image
ECX, ECY, ERX, ERY = 512, 470, 500, 560
def eye_anchor(S, fr, eyes):
    pts = np.concatenate([S[e]['verts']['xyz'].astype(np.float64) for e in eyes]); lat = pts[:, fr['lat']]
    a = pts[lat > np.median(lat)].mean(0); b = pts[lat <= np.median(lat)].mean(0)
    return (a + b) / 2, abs(a[fr['lat']] - b[fr['lat']])
def smooth(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def bilinear(img, x, y):
    h, w, _ = img.shape; x = np.clip(x, 0, w - 1.001); y = np.clip(y, 0, h - 1.001); x0 = x.astype(int); y0 = y.astype(int); fx = (x - x0)[..., None]; fy = (y - y0)[..., None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)
def bake(zt_raw, orig_iwi, face_png, heads=None):
    SS = {'zt': xsurf2.parse(open(zt_raw, 'rb').read())}
    heads = heads or find_heads(SS['zt'])
    if not heads: sys.exit('no head surfaces found: is ZT_RAW the numerically joined, decompressed zombie_theater.ff?')
    atlas = np.asarray(iwilib.to_image(orig_iwi), np.float32).copy(); H, W, _ = atlas.shape
    photo = np.clip(np.asarray(Image.open(face_png).convert('RGB'), np.float32) * float(__import__('os').environ.get('FACE_GAIN', '1.5')), 0, 255)   # game lighting is dark: brighten
    sat = float(__import__('os').environ.get('FACE_SAT', '1.0')); lum = photo.mean(2, keepdims=True); photo = np.clip(lum + (photo - lum) * sat, 0, 255)   # optional saturation boost
    best = np.zeros((H, W), np.float32); out = atlas.copy(); stats = []
    pc = np.array([(PUPILS[0][0] + PUPILS[1][0]) / 2, (PUPILS[0][1] + PUPILS[1][1]) / 2]); pd = PUPILS[1][0] - PUPILS[0][0]
    for src, hi, fk, eyes in heads:
        S = SS[src]; fr = FR[fk]; s = S[hi]; v = s['verts']; xyz = v['xyz'].astype(np.float64); uv = xsurf2.uv(v).astype(np.float64)
        cen, sep = eye_anchor(S, fr, eyes); scale = pd / sep; head_c = xyz.mean(0)
        px_ = lambda P: pc[0] + (P[..., fr['lat']] - cen[fr['lat']]) * scale     # photo right = +lateral axis
        py_ = lambda P: pc[1] - (P[..., fr['up']] - cen[fr['up']]) * scale
        tx = uv[:, 1] * W; ty = uv[:, 0] * H; n_painted = 0
        for a, b, c in s['tris']:
            P = xyz[[a, b, c]]; n = np.cross(P[1] - P[0], P[2] - P[0]); ln = np.linalg.norm(n)
            if ln < 1e-9: continue
            n /= ln
            if n @ (P.mean(0) - head_c) < 0: n = -n
            al = smooth(0.22, 0.62, n[fr['front']])
            if al <= 0: continue
            T = np.stack([tx[[a, b, c]], ty[[a, b, c]]], 1)
            if T[:, 0].max() - T[:, 0].min() > W / 2 or T[:, 1].max() - T[:, 1].min() > H / 2: continue   # wrapped seam triangle
            x0, x1 = max(int(np.floor(T[:, 0].min() - 1)), 0), min(int(np.ceil(T[:, 0].max() + 1)), W - 1); y0, y1 = max(int(np.floor(T[:, 1].min() - 1)), 0), min(int(np.ceil(T[:, 1].max() + 1)), H - 1)
            if x1 < x0 or y1 < y0: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            d0 = (T[1, 1] - T[2, 1]) * (T[0, 0] - T[2, 0]) + (T[2, 0] - T[1, 0]) * (T[0, 1] - T[2, 1])
            if abs(d0) < 1e-9: continue
            w0 = ((T[1, 1] - T[2, 1]) * (gx - T[2, 0]) + (T[2, 0] - T[1, 0]) * (gy - T[2, 1])) / d0
            w1 = ((T[2, 1] - T[0, 1]) * (gx - T[2, 0]) + (T[0, 0] - T[2, 0]) * (gy - T[2, 1])) / d0; w2 = 1 - w0 - w1
            eps = -0.06; m = (w0 >= eps) & (w1 >= eps) & (w2 >= eps)
            if not m.any(): continue
            w0c, w1c, w2c = np.clip(w0, 0, 1), np.clip(w1, 0, 1), np.clip(w2, 0, 1); ws = w0c + w1c + w2c; w0c, w1c, w2c = w0c / ws, w1c / ws, w2c / ws
            pos = w0c[..., None] * P[0] + w1c[..., None] * P[1] + w2c[..., None] * P[2]
            PX, PY = px_(pos), py_(pos); col = bilinear(photo, PX, PY)
            r = np.sqrt(((PX - ECX) / ERX) ** 2 + ((PY - ECY) / ERY) ** 2); mk = 1 - smooth(0.72, 1.0, r)
            reg_best = best[y0:y1 + 1, x0:x1 + 1]; reg_out = out[y0:y1 + 1, x0:x1 + 1]
            upd = m & (al > reg_best)
            A = al * mk; reg_out[upd] = atlas[y0:y1 + 1, x0:x1 + 1][upd] * (1 - A[upd][:, None]) + col[upd] * A[upd][:, None]; reg_best[upd] = al; n_painted += int(upd.sum())
        stats.append((src, hi, round(float(scale), 1), n_painted))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), best, stats
if __name__ == '__main__':
    zt, tpl, face, out = sys.argv[1:5]
    img, best, stats = bake(zt, tpl, face); print('heads (raw, surface, px/unit, texels painted):', stats)
    iwilib.write(tpl, img, out); print('wrote', out)
    if '--preview' in sys.argv: img.save(sys.argv[sys.argv.index('--preview') + 1] + '_atlas.png')
