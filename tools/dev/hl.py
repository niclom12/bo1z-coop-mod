#!/usr/bin/env python3
"""hl.py: tiny HEADLESS Chrome driver over CDP (websockets). Never opens a window: --headless=new + DISPLAY/WAYLAND_DISPLAY unset.
Import: from hl import Browser. Profiles live under $BO1Z_TMP/prof-<name> (default ./tmp). Needs `pip install websockets` and a Chrome/Chromium binary: set CHROME=/path/to/chrome."""
import asyncio, json, os, subprocess, time, base64, urllib.request, shutil
import websockets
CH = os.environ.get('CHROME', 'google-chrome')
EXT = os.path.abspath(os.environ.get('BO1Z_EXT', 'build/coop-extension'))   # output of scripts/patch-extension.sh
TMP = os.path.abspath(os.environ.get('BO1Z_TMP', 'tmp')); os.makedirs(TMP, exist_ok=True)

class Browser:
    def __init__(self, name, port, ext=False, fresh=True, gpu='vulkan', sink=os.environ.get('PULSE_SINK'), size='1440,900'):
        self.name, self.port = name, port
        self.prof = f'{TMP}/prof-{name}'
        if fresh: shutil.rmtree(self.prof, ignore_errors=True)
        args = [CH, '--headless=new', f'--user-data-dir={self.prof}', f'--remote-debugging-port={port}', '--no-sandbox',
                '--ignore-certificate-errors', '--no-first-run', '--no-default-browser-check', f'--window-size={size}',
                '--autoplay-policy=no-user-gesture-required', '--enable-unsafe-webgpu', '--ignore-gpu-blocklist',
                '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows']
        if gpu == 'vulkan': args += ['--enable-features=Vulkan', '--use-angle=vulkan']
        if gpu == 'swiftshader': args += ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']
        if ext: args += [f'--load-extension={EXT}', f'--disable-extensions-except={EXT}']
        args.append('about:blank')
        env = {k: v for k, v in os.environ.items() if k not in ('DISPLAY', 'WAYLAND_DISPLAY')}
        if sink: env['PULSE_SINK'] = sink
        self.log = open(f'{TMP}/chrome-{name}.log', 'w')
        self.proc = subprocess.Popen(args, env=env, stdout=self.log, stderr=self.log, start_new_session=True)
    async def connect(self, tries=60):
        for _ in range(tries):
            try:
                tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{self.port}/json'))
                pg = [t for t in tabs if t['type'] == 'page'][0]; break
            except Exception: await asyncio.sleep(0.5)
        else: raise RuntimeError('no cdp')
        self.ws = await websockets.connect(pg['webSocketDebuggerUrl'], max_size=2**28); self.id = 0; self.pend = {}; self.events = []; self.console = []
        self.t = asyncio.create_task(self._rx())
        for d in ('Page', 'Runtime', 'Network', 'Log'): await self.cmd(f'{d}.enable')
    async def _rx(self):
        async for m in self.ws:
            m = json.loads(m)
            if 'id' in m:
                f = self.pend.pop(m['id'], None)
                if f and not f.done(): f.set_result(m)
            else:
                p = m.get('method', ''); q = m.get('params', {})
                if p == 'Runtime.consoleAPICalled': self.console.append(('console.' + q['type'], ' '.join(str(a.get('value', a.get('description', ''))) for a in q['args'])[:500]))
                elif p == 'Runtime.exceptionThrown': self.console.append(('exception', json.dumps(q['exceptionDetails'])[:500]))
                elif p == 'Log.entryAdded': self.console.append(('log.' + q['entry']['level'], q['entry']['text'][:300] + ' ' + q['entry'].get('url', '')))
                elif p == 'Network.loadingFailed': self.events.append(('netfail', q.get('errorText'), q.get('requestId')))
                elif p == 'Network.responseReceived' and q['response']['status'] >= 400: self.events.append(('http', q['response']['status'], q['response']['url']))
                elif p == 'Network.requestWillBeSent': self.events.append(('req', q['request']['url']))
    async def cmd(self, method, **params):
        self.id += 1; f = asyncio.get_event_loop().create_future(); self.pend[self.id] = f
        await self.ws.send(json.dumps({'id': self.id, 'method': method, 'params': params}))
        r = await asyncio.wait_for(f, 300)
        if 'error' in r: raise RuntimeError(f'{method}: {r["error"]}')
        return r['result']
    async def ev(self, js, await_=False):
        r = await self.cmd('Runtime.evaluate', expression=js, returnByValue=True, awaitPromise=await_)
        if 'exceptionDetails' in r: raise RuntimeError(json.dumps(r['exceptionDetails'])[:400])
        return r['result'].get('value')
    async def init_script(self, js): await self.cmd('Page.addScriptToEvaluateOnNewDocument', source=js)
    async def goto(self, url): await self.cmd('Page.navigate', url=url)
    async def shot(self, path, clip=None):
        r = await self.cmd('Page.captureScreenshot', format='png'); open(path, 'wb').write(base64.b64decode(r['data']))
    async def click(self, x, y):
        for t in ('mouseMoved', 'mousePressed', 'mouseReleased'):
            await self.cmd('Input.dispatchMouseEvent', type=t, x=x, y=y, button='left', clickCount=1)
    async def key(self, k, down=True, up=True, code=None, vk=None, text=None):
        base = dict(key=k, code=code or k, windowsVirtualKeyCode=vk or (ord(k.upper()) if len(k) == 1 else 0))
        if down: await self.cmd('Input.dispatchKeyEvent', type='keyDown', **base, **({'text': text} if text else {}))
        if up: await self.cmd('Input.dispatchKeyEvent', type='keyUp', **base)
    async def move(self, dx, dy):  # relative mouse (pointer lock)
        await self.cmd('Input.dispatchMouseEvent', type='mouseMoved', x=700, y=400, deltaX=dx, deltaY=dy)
    def close(self):
        try: self.proc.terminate(); self.proc.wait(10)
        except Exception: self.proc.kill()
