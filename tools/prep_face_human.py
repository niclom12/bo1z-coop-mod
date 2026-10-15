#!/usr/bin/env python3
"""prep_face_human.py IN.png OUT.png : remove the light studio background of the human face texture. Builds a foreground mask (colour distance from the
background colour sampled at the corners, feathered), then replaces background pixels by blurred nearby foreground colour (hair/skin), so no white
shows through between curls when the bake paints it. Output is opaque RGB 1024x1024 (the bake script has no alpha)."""
import sys, numpy as np
from PIL import Image, ImageFilter
im = Image.open(sys.argv[1]).convert('RGB'); a = np.asarray(im, np.float32)
bg = np.median(np.concatenate([a[:40, :40].reshape(-1, 3), a[:40, -40:].reshape(-1, 3), a[-1:, :40].reshape(-1, 3)]), 0)
d = np.linalg.norm(a - bg, axis=2)
warm = a[..., 0] - a[..., 2]; luma = a.mean(2)
m = np.maximum(np.clip((warm - 16) / 16, 0, 1), np.clip((d - 40) / 25, 0, 1))   # warm (skin/hair) or clearly different from the neutral background
m = np.maximum(m, np.clip((190 - luma) / 30, 0, 1))
m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255
def blur(x, r): return np.asarray(Image.fromarray(x.astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32)
num = np.stack([np.asarray(Image.fromarray((a[..., c] * m).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(24)), np.float32) for c in range(3)], -1)
den = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(24)), np.float32)[..., None] / 255
hair = (a * m[..., None]).sum((0, 1)) / max(float(m.sum()), 1.0)   # fallback where no foreground is near: the average foreground colour
k = np.clip(den * 3, 0, 1)
fill = num / np.maximum(den, 1e-3) * k + hair * (1 - k)
out = a * m[..., None] + fill * (1 - m[..., None])
Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(sys.argv[2])
Image.fromarray((m * 255).astype(np.uint8)).save(sys.argv[2].replace('.png', '_mask.png'))
print('bg', bg, 'fg fraction', float(m.mean()))
