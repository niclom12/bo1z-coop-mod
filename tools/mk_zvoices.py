#!/usr/bin/env python3
"""mk_zvoices.py IN_sounds.pack OUT_sounds.pack CLIP_A CLIP_B
Replaces the audio of every ALIVE zombie vocal alias file in a web build's sounds.pack with one of two clips, alternating by variant index inside
each alias directory (even index -> clip A, odd -> clip B) so the engine's random variant pick gives about 50/50.
Replaced: sound\\vox\\zmb\\standard\\{amb,attack,behind,crawl,sprint,taunt,elec} and sound\\vox\\zmb\\quads\\{ambient,attack,spawn}.
NOT replaced: death, thief, engineer, hellhounds, monkeys, announcer, anything else.
CLIP_A / CLIP_B: any audio file ffmpeg can read (44.1 kHz wav is best). They are encoded here to MS ADPCM mono 44100 block 1024, because the engine's
side table only accepts the retail format (PCM16 gives 'side table miss'). Each alias file gets its own clip (a few samples of different trailing silence),
because the engine did not accept one clip shared by many aliases. The KSIX entry sha (e[3]) stays the retail value on purpose.
Env ZV_MODE=full (default) stores the clip's real length; ZV_MODE=fit pads/truncates to the retail clip length (old behaviour, shorter voices)."""
import sys, re, hashlib, os, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ksp
if len(sys.argv) != 5: sys.exit(__doc__)
src, dst, a, b = sys.argv[1:5]
for p in (a, b):
    if not os.path.isfile(p): sys.exit('clip not found: ' + p)
FULL = os.environ.get('ZV_MODE', 'full') == 'full'
RX = re.compile(r'^sound\\vox\\zmb\\(standard\\(amb|attack|behind|crawl|sprint|taunt|elec)|quads\\(ambient|attack|spawn))\\[^\\]*?(\d+)\.\w+$', re.I)
ver, recs, idx, kver, ents = ksp.load(src); by = {r[0]: r for r in recs}; n = {0: 0, 1: 0}
def encode(clip, i, orig):
    t = tempfile.mktemp(suffix='.wav')
    af = ('apad=pad_len=%d' % (i * 7)) if FULL else ('apad=whole_len=%d' % orig)   # FULL: a few extra silent samples make each alias file's clip unique
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', clip, '-af', af, '-ac', '1', '-ar', '44100', '-c:a', 'adpcm_ms', '-block_size', '1024', t], check=True)
    w = open(t, 'rb').read()
    fr = int(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=duration_ts', '-of', 'csv=p=0', t], capture_output=True, text=True).stdout)
    os.unlink(t); sh = hashlib.sha256(w).digest(); return w, sh, 'clips/' + sh.hex() + '.wav', fr
srcs = (a, b); cnt = 0
for e in ents:
    m = RX.match(e[0])
    if not m: continue
    k = int(m.group(4)) % 2; cnt += 1; orig = e[2]
    w, sh, nm, frames = encode(srcs[k], cnt, orig); frames = frames if FULL else orig
    if nm not in by: r = [nm, 1, w, sh]; recs.append(r); by[nm] = r
    e[1], e[2] = nm, frames   # e[3] (KSIX sha) stays the retail value: the engine rejects an entry whose sha differs
    n[k] += 1
if not cnt: sys.exit('no zombie vocal aliases found: is IN_sounds.pack the retail Kino pack?')
refs = {e[1] for e in ents}; recs[:] = [r for r in recs if r[1] == 0 or r[0] in refs]
idx[2] = ksp.ksix_wr(kver, ents); idx[3] = hashlib.sha256(idx[2]).digest()
open(dst, 'wb').write(ksp.wr(ver, recs)); print('replaced clip A (even):', n[0], 'clip B (odd):', n[1], 'records', len(recs))
