"""render_mesh: tiny software renderer (orthographic, z-buffer, texture lookup by uv, optional lambert) for checking UV/face mapping offline. numpy+Pillow."""
import numpy as np
from PIL import Image
def render(xyz, uv, tris, tex, view_dir, up=(0, 0, 1), size=512, flipv=False, shade=True, normals=None, pad=0.08):
    """view_dir: unit vector from object toward camera. Returns RGB image."""
    f = np.asarray(view_dir, float); f /= np.linalg.norm(f); r = np.cross(up, f); r /= np.linalg.norm(r); u = np.cross(f, r)
    P = np.stack([xyz @ r, xyz @ u, xyz @ f], 1)
    mn, mx = P[:, :2].min(0), P[:, :2].max(0); sc = (1 - 2 * pad) * size / max(mx - mn); off = (size - (mx - mn) * sc) / 2
    X = (P[:, 0] - mn[0]) * sc + off[0]; Y = size - ((P[:, 1] - mn[1]) * sc + off[1]); Z = P[:, 2]
    T = np.asarray(tex.convert('RGB'), np.float32); th, tw = T.shape[:2]
    img = np.zeros((size, size, 3), np.float32); zb = np.full((size, size), -1e9, np.float32)
    for a, b, c in tris:
        x0, x1, x2 = X[[a, b, c]]; y0, y1, y2 = Y[[a, b, c]]
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-6: continue
        # backface cull (camera looks from +f): geometric normal facing
        n = np.cross(xyz[b] - xyz[a], xyz[c] - xyz[a]); facing = n @ f
        xa, xb = int(max(0, np.floor(min(x0, x1, x2)))), int(min(size - 1, np.ceil(max(x0, x1, x2))))
        ya, yb = int(max(0, np.floor(min(y0, y1, y2)))), int(min(size - 1, np.ceil(max(y0, y1, y2))))
        if xb < xa or yb < ya: continue
        gx, gy = np.meshgrid(np.arange(xa, xb + 1) + .5, np.arange(ya, yb + 1) + .5)
        w0 = ((x1 - gx) * (y2 - gy) - (x2 - gx) * (y1 - gy)) / area; w1 = ((x2 - gx) * (y0 - gy) - (x0 - gx) * (y2 - gy)) / area; w2 = 1 - w0 - w1
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not m.any(): continue
        z = w0 * Z[a] + w1 * Z[b] + w2 * Z[c]; sub = zb[ya:yb + 1, xa:xb + 1]; m &= z > sub
        if not m.any(): continue
        uu = w0 * uv[a, 0] + w1 * uv[b, 0] + w2 * uv[c, 0]; vv = w0 * uv[a, 1] + w1 * uv[b, 1] + w2 * uv[c, 1]
        if flipv: vv = 1 - vv
        tx = np.clip((uu * tw).astype(int) % tw, 0, tw - 1); ty = np.clip((vv * th).astype(int) % th, 0, th - 1)
        col = T[ty, tx]
        if shade: col = col * (0.45 + 0.55 * abs(facing) / (np.linalg.norm(n) + 1e-9))
        reg = img[ya:yb + 1, xa:xb + 1]; reg[m] = col[m]; sub[m] = z[m]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
