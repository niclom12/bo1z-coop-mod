#!/usr/bin/env python3
"""coop_session.py : two HEADLESS Chrome profiles with the co-op extension; host + guest through the local relay.
Usage: coop_session.py --origin https://LAN_IP:20100 --relay https://LAN_IP:20000 --out OUTPREFIX [--secs 60]
Flow: host opens <origin>/bo1z/kino.html?coop=host&room=CODE, guest opens ?coop=join&room=CODE; both use the relay given by --relay
(localStorage bo1coop.relay, set before the page scripts run). Dumps the extension card text and screenshots every few seconds."""
import sys, asyncio, argparse, json, random, time
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import hl, game
ap = argparse.ArgumentParser(); ap.add_argument('--origin', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--secs', type=int, default=60); ap.add_argument('--relay', required=True); ap.add_argument('--page', default='kino.html')
a = ap.parse_args()
ALPHA = 'abcdefghjkmnpqrstuvwxyz23456789'
def code(): return '-'.join(''.join(random.choice(ALPHA[:30]) for _ in range(4)) for _ in range(4))
CARD = '''(() => { const r = document.querySelector('#bo1coop-root, [id*=coop]'); const t = []; const walk = (n) => { if (n.shadowRoot) walk(n.shadowRoot); for (const c of n.children || []) walk(c); };
  const out = []; const all = document.querySelectorAll('*'); for (const e of all) if (e.shadowRoot) out.push(e.shadowRoot.textContent.replace(/\\s+/g,' ').slice(0, 600)); return out.join(' || '); })()'''
async def main():
    room = code(); print('room', room, flush=True)
    h = hl.Browser('coopH', 29501, ext=True); g = hl.Browser('coopG', 29502, ext=True)
    try:
        await h.connect(); await g.connect()
        for b in (h, g):
            await b.init_script("try{localStorage.setItem('bo1coop.relay','%s')}catch(e){}" % a.relay)
        await h.goto(f'{a.origin}/bo1z/{a.page}?coop=host&room={room}')
        await asyncio.sleep(6)
        await g.goto(f'{a.origin}/bo1z/{a.page}?coop=join&room={room}')
        t0 = time.time(); n = 0; clicked = {'h': 0, 'g': 0}
        while time.time() - t0 < a.secs:
            for nm, b in (('h', h), ('g', g)):
                try: s = await game.st(b)
                except Exception: s = {}
                if n % 3 == 0:
                    print(round(time.time() - t0), nm, s.get('screen'), s.get('play'), s.get('tr', '')[:40], '|', (await b.ev(CARD))[:300] if True else '', flush=True)
                    await b.shot(f'{a.out}-{nm}-{n:03d}.png')
                if s.get('play') and not s.get('dis') and not s.get('hidden') and s.get('screen') in ('landing', 'ready') and s.get('play') != 'Loading' and time.time() - clicked[nm] > 8:
                    await b.click(720, 450); clicked[nm] = time.time()
            n += 1; await asyncio.sleep(3)
        for nm, b in (('h', h), ('g', g)):
            await b.shot(f'{a.out}-{nm}-end.png')
            print('ERRORS', nm, json.dumps([c for c in b.console if c[0] in ('exception', 'log.error', 'console.error')][:30]), json.dumps([e for e in b.events if e[0] in ('http', 'netfail')]), flush=True)
    finally:
        h.close(); g.close()
asyncio.run(main())
