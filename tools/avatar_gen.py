#!/usr/bin/env python3
"""avatar_gen.py KIND REFERENCE_PHOTO [N_TAKES] [MODEL] : generate zombie-face source images from a photo with an image-editing model on OpenRouter.
KIND: portrait | front_zombie | front_human
  portrait      a head-and-shoulders zombie portrait (for fun / a profile picture)
  front_zombie  a flat, front-facing, evenly lit zombie face (texture source for make-face.sh)
  front_human   the same but a clean natural face (best for the in-game head: the game's own lighting adds the zombie look)
Output PNGs go to $AVATAR_OUT (default ./avatar-out). Needs OPENROUTER_API_KEY, Pillow. Default model google/gemini-3-pro-image (about $0.14 per image).
Only use a photo of yourself or of someone who agreed to it."""
import base64, json, os, sys, time, urllib.request, io
from PIL import Image
KEY = os.environ.get('OPENROUTER_API_KEY')
if not KEY:
    sys.exit('OPENROUTER_API_KEY is not set. Get a key at https://openrouter.ai/keys and run: export OPENROUTER_API_KEY=...')
if len(sys.argv) < 3 or sys.argv[1] not in ('portrait', 'front_zombie', 'front_human'):
    sys.exit(__doc__)
D = os.environ.get('AVATAR_OUT', './avatar-out'); os.makedirs(D, exist_ok=True)
ID = ("Use the reference photo ONLY for the person's identity: keep the exact face shape, brow, nose, eyes, hair style and colour, and any facial hair. "
      "Ignore lens flare, reflections and the photo background. ")
P = {
 "portrait": ID + "Create a Call of Duty: Black Ops 1 (2010) Nazi-zombie style head-and-shoulders portrait of this person as a zombie: "
   "grey-green decayed rotting skin, glowing orange-yellow eyes (BO1 zombie eye glow), sunken cheeks, open wounds, torn flesh, grime and dirt, "
   "matted hair and facial hair still recognisable, tattered dark clothing. Front-facing, neutral dark background, 2010 video game art realism. Square.",
 "front_zombie": ID + "Create a FLAT texture-source image of this person's face as a Black Ops 1 zombie: perfectly front-facing, straight-on orthographic view, "
   "neutral expression, eyes open and looking straight ahead, mouth closed, head upright and symmetric, flat even diffuse lighting with NO shadows and no highlights, "
   "no background: the frame is filled edge to edge by the face, with hair at top and sides and neck/skin at the bottom. "
   "Grey-green decayed skin, subtle wounds and grime, eyes glowing orange-yellow, facial hair kept. Square, face centred and filling the frame.",
 "front_human": ID + "Create a FLAT texture-source image of this person's clean, healthy, natural face: perfectly front-facing, straight-on, neutral expression, eyes open looking straight ahead, "
   "mouth closed, head upright and symmetric, flat even diffuse lighting with NO shadows or highlights, no background: the frame is filled edge to edge by the face, "
   "hair at top and sides, neck at the bottom. Natural skin tone, facial hair kept. Square, face centred and filling the frame.",
}
kind, ref = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 3
model = sys.argv[4] if len(sys.argv) > 4 else "google/gemini-3-pro-image"
im = Image.open(ref).convert("RGB"); im.thumbnail((1280, 1280))
b = io.BytesIO(); im.save(b, "JPEG", quality=92); url = "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
for i in range(n):
    body = {"model": model, "modalities": ["image", "text"], "image_config": {"aspect_ratio": "1:1"},
            "messages": [{"role": "user", "content": [{"type": "text", "text": P[kind]}, {"type": "image_url", "image_url": {"url": url}}]}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    try: r = json.load(urllib.request.urlopen(req, timeout=300))
    except Exception as e: print("ERR", e, getattr(e, 'read', lambda: b'')()[:300]); continue
    msg = r["choices"][0]["message"]; imgs = msg.get("images") or []
    print(kind, i, "cost:", r.get("usage", {}).get("cost"), "images:", len(imgs))
    for j, im_ in enumerate(imgs):
        data = base64.b64decode(im_["image_url"]["url"].split(",", 1)[1])
        fn = f"{D}/{kind}_{int(time.time())}_{i}_{j}.png"; open(fn, "wb").write(data); print(fn)
