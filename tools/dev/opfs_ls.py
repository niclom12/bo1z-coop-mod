#!/usr/bin/env python3
"""opfs_ls.py NAME PORT URL PATH : headless; list an OPFS directory (e.g. pack-kino/files/mods) of the profile prof-NAME (not wiped)."""
import sys, asyncio, json
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import hl
async def main():
    name, port, url, path = sys.argv[1:5]; b = hl.Browser(name, port, fresh=False)
    try:
        await b.connect(); await b.goto(url); await asyncio.sleep(2)
        js = '''(async()=>{let d=await navigator.storage.getDirectory();for(const p of %r.split('/')){if(p)d=await d.getDirectoryHandle(p)}
        const out=[];async function w(h,pre){for await(const [n,e] of h.entries()){if(e.kind==='directory')await w(e,pre+n+'/');else out.push(pre+n+' '+(await e.getFile()).size)}}await w(d,'');return out})()''' % path
        for l in await b.ev(js, True): print(l)
    finally: b.close()
asyncio.run(main())
