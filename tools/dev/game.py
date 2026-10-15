"""game.py: helpers to drive the web build headlessly (landing -> download/load -> ready -> in game)."""
import asyncio, json, time
SJS = '''(() => { const g = id => document.getElementById(id); const t = e => e ? e.textContent.trim() : '';
  return JSON.stringify({screen: document.body.dataset.screen, status: t(g('status')), play: t(g('play')), dis: !!g('play')?.disabled, hidden: !!g('play')?.hidden,
  err: t(g('error-message')), tr: t(g('transfer-details')), ld: t(g('load-details')), lock: document.pointerLockElement ? 1 : 0, hint: !g('resume-hint')?.hidden}) })()'''
async def st(b): return json.loads(await b.ev(SJS))
async def start(b, url, timeout=1800, log=print, mods=None):
    if mods is not None:
        await b.init_script("try{localStorage.setItem('__x','1')}catch(e){}")
    await b.goto(url); t0 = time.time(); last = None; clicked = False
    while time.time() - t0 < timeout:
        try: s = await st(b)
        except Exception as e: await asyncio.sleep(1); continue
        k = (s['screen'], s['play'], s['dis'], s['tr'][:30], s['ld'][:30], s['err'][:60])
        if k != last: log(round(time.time() - t0), s); last = k
        if s['err']: raise RuntimeError('page error: ' + s['err'])
        if s['screen'] == 'playing': return s
        if s['play'] and not s['dis'] and not s['hidden'] and s['screen'] in ('landing', 'ready') and s['play'] != 'Loading':
            if s['screen'] == 'ready' or not clicked or s['screen']=='landing':
                await b.click(720, 450); clicked = True
                await asyncio.sleep(2)
        await asyncio.sleep(1)
    raise TimeoutError('start timeout')
async def jserrors(b): return [c for c in b.console if c[0] in ('exception', 'log.error', 'console.error')]
