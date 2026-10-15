"""iwilib: read/write BO1 IWi (v13) DXT1 images (largest mip first). Needs numpy + Pillow. Run with `python3 -P` (not -I: -I hides user site)."""
import struct, numpy as np
from PIL import Image
HDR = 48
def info(d):
    assert d[:3] == b'IWi' and d[4] == 0x0B, 'DXT1 IWi only (fmt %r)' % d[4:5]
    w, h, depth = struct.unpack('<3H', d[6:12]); sizes = struct.unpack('<8I', d[16:48]); return w, h, sizes
def mip_dims(w, h):
    out = []
    while True:
        out.append((w, h))
        if w == 1 and h == 1: return out
        w, h = max(1, w // 2), max(1, h // 2)
def blocks_bytes(w, h): return max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * 8
def decode_dxt1(b, w, h):
    bw, bh = max(1, (w + 3) // 4), max(1, (h + 3) // 4)
    a = np.frombuffer(b, dtype='<u2', count=bw * bh * 4).reshape(bh, bw, 4); c0, c1 = a[..., 0].astype(np.int32), a[..., 1].astype(np.int32)
    idx = (a[..., 2].astype(np.uint32) | (a[..., 3].astype(np.uint32) << 16))
    def rgb(c): return np.stack([((c >> 11) & 31) * 255 // 31, ((c >> 5) & 63) * 255 // 63, (c & 31) * 255 // 31], -1)
    p0, p1 = rgb(c0), rgb(c1); four = (c0 > c1)[..., None]
    p2 = np.where(four, (2 * p0 + p1) // 3, (p0 + p1) // 2); p3 = np.where(four, (p0 + 2 * p1) // 3, 0)
    pal = np.stack([p0, p1, p2, p3], 2)  # bh,bw,4,3
    out = np.zeros((bh * 4, bw * 4, 3), np.uint8)
    for py in range(4):
        for px in range(4):
            s = (idx >> (2 * (py * 4 + px))) & 3
            out[py::4, px::4] = np.take_along_axis(pal, s[..., None, None].astype(np.int64).repeat(3, -1), 2)[:, :, 0, :]
    return out[:h, :w]
def read(path):
    d = open(path, 'rb').read(); w, h, sizes = info(d); pos = HDR; mips = [None] * len(mip_dims(w, h))
    # data order on disk: SMALLEST mip first, largest last (fileSizeForPicmip[k] is a prefix of the file, so lower picmips read less)
    for k in reversed(range(len(mips))):
        mw, mh = mip_dims(w, h)[k]; n = blocks_bytes(mw, mh); mips[k] = d[pos:pos + n]; pos += n
    assert pos == len(d) == sizes[0], (pos, len(d), sizes[0])
    return d[:HDR], w, h, mips
def to_image(path, mip=0):
    hdr, w, h, mips = read(path); mw, mh = mip_dims(w, h)[mip]; return Image.fromarray(decode_dxt1(mips[mip], mw, mh))
def encode_dxt1(rgb):
    """rgb: HxWx3 uint8 (dims multiple of 4 or <4 padded by edge repeat). Bounding-box endpoints along the principal axis, 4-colour mode."""
    h, w, _ = rgb.shape; ph, pw = max(4, (h + 3) // 4 * 4), max(4, (w + 3) // 4 * 4)
    if (ph, pw) != (h, w): rgb = np.pad(rgb, ((0, ph - h), (0, pw - w), (0, 0)), mode='edge')
    bh, bw = ph // 4, pw // 4
    B = rgb.reshape(bh, 4, bw, 4, 3).transpose(0, 2, 1, 3, 4).reshape(bh * bw, 16, 3).astype(np.float32)
    mean = B.mean(1, keepdims=True); C = B - mean
    cov = np.einsum('npi,npj->nij', C, C); wv, ev = np.linalg.eigh(cov); axis = ev[:, :, -1]  # n,3
    proj = np.einsum('npi,ni->np', C, axis); lo, hi = proj.min(1), proj.max(1)
    e0 = np.clip(mean[:, 0] + axis * hi[:, None], 0, 255); e1 = np.clip(mean[:, 0] + axis * lo[:, None], 0, 255)
    def q(e): return (np.round(e[:, 0] * 31 / 255).astype(np.int32) << 11) | (np.round(e[:, 1] * 63 / 255).astype(np.int32) << 5) | np.round(e[:, 2] * 31 / 255).astype(np.int32)
    c0, c1 = q(e0), q(e1)
    # 4-colour mode needs c0 > c1; equal -> nudge
    sw = c0 < c1; c0, c1 = np.where(sw, c1, c0), np.where(sw, c0, c1)
    eq = c0 == c1
    def rgbf(c): return np.stack([((c >> 11) & 31) * 255 / 31, ((c >> 5) & 63) * 255 / 63, (c & 31) * 255 / 31], -1).astype(np.float32)
    p0, p1 = rgbf(c0), rgbf(c1); pal = np.stack([p0, p1, (2 * p0 + p1) / 3, (p0 + 2 * p1) / 3], 1)  # n,4,3
    # for equal endpoints all pixels index 0
    dist = ((B[:, :, None, :] - pal[:, None, :, :]) ** 2).sum(-1)  # n,16,4
    ix = dist.argmin(-1); ix[eq] = 0
    bits = np.zeros(len(B), np.uint32)
    for p in range(16): bits |= ix[:, p].astype(np.uint32) << (2 * p)
    out = np.zeros((len(B), 8), np.uint8)
    out[:, 0:2] = c0.astype('<u2').view(np.uint8).reshape(-1, 2); out[:, 2:4] = c1.astype('<u2').view(np.uint8).reshape(-1, 2); out[:, 4:8] = bits.astype('<u4').view(np.uint8).reshape(-1, 4)
    return out.tobytes()
def write(template, img, out):
    """Encode PIL image (resized to template dims) with the template's header/mip chain, all mips from the box-filtered full image."""
    hdr, w, h, mips = read(template); img = img.convert('RGB').resize((w, h), Image.LANCZOS) if img.size != (w, h) else img.convert('RGB')
    parts = []
    for (mw, mh) in mip_dims(w, h):
        im = img if (mw, mh) == (w, h) else img.resize((mw, mh), Image.BOX)
        parts.append(encode_dxt1(np.asarray(im)))
    data = b''.join(reversed(parts))  # smallest mip first
    open(out, 'wb').write(hdr + data)
