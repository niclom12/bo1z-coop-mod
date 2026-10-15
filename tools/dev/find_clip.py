#!/usr/bin/env python3
"""find_clip.py CAPTURE.wav CLIP.wav [CLIP2.wav ...] : normalized cross-correlation of each clip against a recording (mono s16, same rate).
Prints best peak value (0..1) and time offsets of peaks > 0.5*best. Used to prove a replaced sound really plays in the browser."""
import sys, wave, numpy as np
def load(p):
    w = wave.open(p); assert w.getsampwidth() == 2
    x = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float32)
    if w.getnchannels() > 1: x = x.reshape(-1, w.getnchannels()).mean(1)
    return x, w.getframerate()
cap, r = load(sys.argv[1]); print('capture', len(cap)/r, 's rms', float(np.sqrt((cap**2).mean())))
for p in sys.argv[2:]:
    c, rc = load(p); assert rc == r, (rc, r)
    n = 1 << int(np.ceil(np.log2(len(cap) + len(c))))
    fc = np.fft.rfft(cap, n); fk = np.fft.rfft(c[::-1], n)
    cc = np.fft.irfft(fc * fk, n)[len(c)-1:len(cap)]
    cs = np.concatenate([[0.0], np.cumsum(cap.astype(np.float64)**2)]); e = np.sqrt(np.maximum(cs[len(c):len(c)+len(cc)] - cs[:len(cc)], 0)).astype(np.float32) * np.linalg.norm(c) + 1e-6
    wen = np.sqrt(np.maximum(cs[len(c):len(c)+len(cc)] - cs[:len(cc)], 0) / len(c)); nc = np.where(wen > 100, cc / e, 0); k = float(nc.max()); idx = np.where(nc > max(0.5*k, 0.3))[0]
    peaks = []
    for i in idx:
        if not peaks or i - peaks[-1] > r: peaks.append(i)
    print(p.split('/')[-1], 'best', round(k, 3), 'at', [round(i / r, 1) for i in peaks][:15])
