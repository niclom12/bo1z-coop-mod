#!/usr/bin/env python3
"""play_session.py: one headless game session. Args: --name N --port P --url URL [--fresh] [--ext] [--secs S] [--shots PREFIX --every E] [--audio OUT.wav]
  [--look "dx,dy"] [--keys "w:2.0,a:1"] [--fire]. With --audio it records PULSE_MONITOR (a PulseAudio monitor source, e.g. a null sink's .monitor) with parec; set PULSE_SINK to the same null sink for the browser.
Prints a JSON summary: console errors, failed requests, state."""
import sys, asyncio, json, time, subprocess, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hl, game
ap = argparse.ArgumentParser()
ap.add_argument('--name', required=True); ap.add_argument('--port', type=int, required=True); ap.add_argument('--url', required=True)
ap.add_argument('--fresh', action='store_true'); ap.add_argument('--ext', action='store_true'); ap.add_argument('--secs', type=float, default=60)
ap.add_argument('--shots'); ap.add_argument('--every', type=float, default=10); ap.add_argument('--audio'); ap.add_argument('--fire', action='store_true')
ap.add_argument('--cmds', default=''); ap.add_argument('--wait-start', type=float, default=0); ap.add_argument('--gpu', default='vulkan')
a = ap.parse_args()
async def main():
    b = hl.Browser(a.name, a.port, ext=a.ext, fresh=a.fresh, gpu=a.gpu)
    rec = None
    try:
        await b.connect()
        if a.cmds: await b.init_script('globalThis.__headlessInput = true; globalThis.__kisakParity = {commands: %s};' % json.dumps(a.cmds.split()))
        s = await game.start(b, a.url, log=lambda *x: print(*x, flush=True))
        print('IN GAME', s, flush=True)
        if a.audio:
            rec = subprocess.Popen(['parec', '-d', os.environ.get('PULSE_MONITOR', 'bo1z_null.monitor'), '--rate=44100', '--channels=1', '--format=s16le', '--file-format=wav', a.audio], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t0 = time.time(); n = 0
        while time.time() - t0 < a.secs:
            if a.shots and time.time() - t0 >= n * a.every:
                await b.shot(f'{a.shots}-{n:02d}.png'); n += 1
            if a.fire: await b.cmd('Input.dispatchMouseEvent', type='mousePressed', x=720, y=450, button='left', clickCount=1); await b.cmd('Input.dispatchMouseEvent', type='mouseReleased', x=720, y=450, button='left', clickCount=1)
            await asyncio.sleep(1)
        await b.shot(f'{a.shots}-end.png') if a.shots else None
        print('GAMELOG', json.dumps([c for c in b.console if any(k in c[1].lower() for k in ('zctest','alias','vocals','sound'))][:400]), flush=True)
        print('SUMMARY', json.dumps({'state': await game.st(b), 'errors': await game.jserrors(b), 'bad': [e for e in b.events if e[0] in ('http', 'netfail')]}), flush=True)
    finally:
        if rec: rec.terminate()
        b.close()
asyncio.run(main())
