#!/usr/bin/env python3
"""stt.py FILE... : transcribe audio with a Gemini model on OpenRouter (used to check that a generated clip says what you asked).
Needs OPENROUTER_API_KEY in the environment and ffmpeg on the PATH. Set STT_MODEL to use another model."""
import sys, json, os, base64, subprocess, urllib.request
key = os.environ.get('OPENROUTER_API_KEY')
if not key:
    sys.exit('OPENROUTER_API_KEY is not set. Get a key at https://openrouter.ai/keys and run: export OPENROUTER_API_KEY=...')
MODEL = os.environ.get('STT_MODEL', 'google/gemini-3.8-flash')
for f in sys.argv[1:]:
    wav = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ar", "16000", "-ac", "1", "-f", "wav", "-"], capture_output=True).stdout
    b = {"model": MODEL, "messages": [{"role": "user", "content": [
        {"type": "text", "text": "Transcribe this audio verbatim, words only, including any punctuation marks you hear. Also say in a few words if the speaker sounds male or female and the emotion."},
        {"type": "input_audio", "input_audio": {"data": base64.b64encode(wav).decode(), "format": "wav"}}]}]}
    r = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(b).encode(), headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try: print(f, "=>", json.load(urllib.request.urlopen(r, timeout=120))["choices"][0]["message"]["content"].replace("\n", " | "))
    except Exception as e: print(f, "ERR", e)
