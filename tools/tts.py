#!/usr/bin/env python3
"""tts.py MODEL VOICE OUT TEXT [INSTRUCTIONS] : text to speech through OpenRouter (/api/v1/audio/speech).
OUT ending in .pcm asks for raw 24 kHz 16-bit mono PCM (what google/gemini-3.1-flash-tts-preview returns); any other name gets mp3.
Needs OPENROUTER_API_KEY in the environment. Example (the em dash clip, see docs/MODDING.md):
  tts.py google/gemini-3.1-flash-tts-preview Charon take.pcm "Say as a deep adult man, shouting in outraged disbelief: Is that an em dash?!!" """
import sys, json, os, urllib.request, urllib.error
key = os.environ.get('OPENROUTER_API_KEY')
if not key:
    sys.exit('OPENROUTER_API_KEY is not set. Get a key at https://openrouter.ai/keys and run: export OPENROUTER_API_KEY=...')
if len(sys.argv) < 5:
    sys.exit(__doc__)
m, v, out, text = sys.argv[1:5]
ins = sys.argv[5] if len(sys.argv) > 5 else None
body = {"model": m, "input": text, "voice": v, "response_format": "pcm" if out.endswith(".pcm") else "mp3"}
if ins: body["instructions"] = ins
r = urllib.request.Request("https://openrouter.ai/api/v1/audio/speech", data=json.dumps(body).encode(),
                           headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(r, timeout=180) as x: open(out, 'wb').write(x.read()); print("ok", out)
except urllib.error.HTTPError as e:
    sys.exit("ERR %s %s %s %s" % (m, v, e.code, e.read()[:300].decode(errors='replace')))
