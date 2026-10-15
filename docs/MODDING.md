# Modding: custom zombie voices and face (Kino der Toten)

This page explains how the voice and face mods work and how to make your own. The scripts do the work; the sections on formats are for people who want to know why, or want to extend it to other maps.

Everything here only reads files you downloaded yourself (`scripts/get-web-build.sh`) and writes changed copies into that same folder. Nothing from the game is stored in this repo. Only mod material you own or have permission to use: use your own voice or generated speech, and a photo of yourself or of someone who agreed.

Quick version:

```
scripts/make-voices.sh [clipA clipB]   # work/mod/kino-sounds.pack
scripts/make-face.sh face.png          # work/mod/c_ger_zombie_head1_c.iwi
scripts/apply-mod.sh                   # into ./web, manifest updated
scripts/restore.sh                     # undo
```

`apply-mod.sh` keeps the untouched originals in `web/.bo1z-backup/` the first time it runs. It applies whatever exists in `work/mod/` (voices, face, or both). Mod files go into the Kino pack only; other maps ship their own packs and zones and would each need their own check.

## 1. Voices

### What gets replaced

The web build keeps all game sounds in one container per map, `kino/pack/web/sound/sounds.pack` (about 70 MB):

- **KSPK container**: a header (`KSPK`, version, record count, header length, total size), then records `{offset, length, fmt, nameLength, sha256, name}`, then the data. `fmt 0` is the index `sounds.bin`; `fmt 1` is a clip, named `clips/<sha256>.wav`.
- **KSIX index** (the contents of `sounds.bin`): entries `{path, clip, frames, sha256}`. `path` is the game's own sound file path (for example `sound\vox\zmb\standard\attack\...`), `clip` the record that holds the audio, `frames` the length in samples.
- `tools/ksp.py` reads and writes both (`ksp.py list PACK REGEX`, `ksp.py roundtrip PACK` to prove a rebuild is byte-identical).

`tools/mk_zvoices.py` replaces the clip of every **living** zombie vocal, 81 files in Kino:

```
sound\vox\zmb\standard\{amb, attack, behind, crawl, sprint, taunt, elec}
sound\vox\zmb\quads\{ambient, attack, spawn}
```

Clip A goes on even variant numbers inside each alias folder, clip B on odd ones, so the game's random variant pick gives about 50/50. Death sounds, the thief, engineer, hellhounds, monkeys and the announcer are not touched. The alias names to know when testing in game are `zmb_vocals_zombie_ambience`, `..._attack`, `..._behind`, `..._sprint` and `..._taunt`; how often they play is the game's own script logic (`do_zombies_playvocals`), unchanged.

### Rules the engine enforces (found by testing)

1. **Clips must be MS ADPCM, mono, 44100 Hz** (block size 1024), like the retail clips. A PCM16 clip makes the engine log `browser sound miss ... (side table miss ...)` for every replaced file and play nothing. The tool encodes with `ffmpeg -c:a adpcm_ms -block_size 1024 -ar 44100 -ac 1`, so you can feed it any normal audio file.
2. **The KSIX entry's sha256 must stay the retail value.** Each entry carries a hash that is not the same as the record's hash; if you update it to match your new clip the engine rejects the entry. The tool leaves it alone and updates only the clip name and the frame count.
3. **`frames` must be the clip's real length** in samples. The tool uses the real length (`ZV_MODE=full`, the default), so the whole clip plays. `ZV_MODE=fit` pads or cuts to the retail length instead, which gives shorter, truncated voices.
4. **Give every alias file its own clip.** The engine's side table did not accept one clip shared by many aliases, so the tool adds a few samples of silence (a different amount per alias file) to make each one unique.
5. The container's own record hashes are recomputed, and `tools/mkmod.py --replace` recomputes the size and sha256 in the map manifest, drops the stale `.kop` (opus) copy, and bumps the manifest version. That is what makes browsers re-download the file.

### Making your own clips

Any two clips of about 1 to 2 seconds work. For text-to-speech, `tools/tts.py` calls OpenRouter's `/api/v1/audio/speech` (set `OPENROUTER_API_KEY`; cost is a fraction of a cent per take):

```
export OPENROUTER_API_KEY=...
python3 -P tools/tts.py google/gemini-3.1-flash-tts-preview Charon take_a.pcm \
  "Say as a deep adult man, shouting in outraged disbelief, rising intonation at the end, very expressive: Is that an em dash?!!"
python3 -P tools/tts.py google/gemini-3.1-flash-tts-preview Achernar take_b.pcm \
  "Say quickly in a bright, cheerful, very high-pitched young girl's voice, sweet and bubbly: Hi Johan!"
```

Those are the two prompts behind the example clips in `examples/voices/`. This model returns raw 24 kHz 16-bit mono PCM (`.pcm`), and takes its delivery from natural-language style text at the start of the input. Take several per voice and pick by ear: delivery varies a lot between takes, and a very high-pitched style can flip a male voice to a female one. Other models tried on OpenRouter: ElevenLabs v3 (preset voices only, calm delivery), Grok voice (calm), MiniMax speech-2.8-hd. Gemini gave the most expressive, shouted delivery.

Turn a take into the final formats with `tools/process.sh`:

```
ffmpeg -f s16le -ar 24000 -ac 1 -i take_a.pcm take_a.wav
tools/process.sh take_a.wav my_clip_a -3 1.12     # IN STEM SEMITONES TEMPO
```

It trims silence at both ends, optionally shifts pitch by semitones (keeping the length) and changes speed, normalises loudness in two passes to -16 LUFS, adds 5 ms fades and a limiter, and writes `clips/my_clip_a.wav` (48 kHz), `my_clip_a_44k.wav`, `.mp3` and `.opus`. The example man clip used `-3 1.12` (a bit lower, a bit faster); the girl clip used `0 1.05`. `tools/pitch.py FILE` prints the median fundamental frequency, handy to check a "deep" voice really is deep. `tools/stt.py FILE` transcribes a clip through a Gemini model on OpenRouter, to confirm it says what you asked.

Then:

```
scripts/make-voices.sh clips/my_clip_a_44k.wav clips/my_clip_b_44k.wav
scripts/apply-mod.sh
```

## 2. Face

### What gets replaced

All Kino zombies of the "head1" type share one head texture, `images/c_ger_zombie_head1_c.iwi` (inside `main/iw_01.iwd`): 512x512, DXT1, 8 mip levels, 174,824 bytes. It is an atlas: four head unwraps (one horizontal strip each) on the left, hands and body on the right. The mod ships a replacement as a **loose file** `mods/zcustom/images/c_ger_zombie_head1_c.iwi`, which overrides the retail image when the `zcustom` mod is on. The site's `play.js` only turns mods on from the Options page, so `tools/patch_playjs.py` adds a line that always adds `zcustom` to `fs_mods` when the map's pack ships `mods/zcustom/...`. `apply-mod.sh` patches from the untouched copy, so it can run repeatedly.

### Image format details that matter

- **IWi v13, DXT1** (format byte `0x0B`), 48-byte header. **Mips are stored smallest first**, largest last. Reading the largest mip from the front gives a garbled picture. `tools/iwilib.py` reads and writes it (DXT1 decode and an encoder; the written file keeps the original header, size, format and full mip chain, with the mips regenerated from the new image).
- **UV convention:** the head meshes' UVs are **transposed**: texel x = `uv[1] * width`, texel y = `uv[0] * height`.
- **The four head surfaces.** There are four head1 variants, each a large surface followed by a small eyeball surface. `tools/xsurf2.py` parses surfaces out of the decompressed zone file; `bake_face.find_heads` finds the four heads by that signature (a surface with 800 or more vertices directly followed by a surface whose UV box is the atlas' eye patch, u .137 to .2 and v .703 to .77). The first is surface 86 in Kino's `zombie_theater.ff`. Other surfaces with similar-looking UVs are not head1_c heads (hair islands, gibs, other characters); painting them puts the face in the wrong place.
- **Join zone chunks in numeric order.** Big zone files are split into `zombie_theater.ff.part/0, 1, 2, ... 13`. Joining them as `0 1 10 11 12 13 2 ...` (what a plain shell sort does) scrambles the file, and surface numbers after the first 16 MiB are then wrong. `make-face.sh` does it right.

### How the bake works (`tools/bake_face.py`)

1. The decompressed zone file (`tools/ffraw.py`: `IWffu100` is a 12-byte header plus a zlib stream, `IWffr100` a 48-byte header plus the raw stream) is parsed for the four heads and their eyeballs.
2. For each head the picture is placed so the pupils in the picture (measured on the 1024x1024 face image, at x=365 and x=655, y=440) sit on the eyeballs; the scale comes from the pupil distance.
3. Every **front-facing** triangle of the head is rasterised into the atlas, sampling the picture by projecting the triangle's 3D position. The paint strength is a smoothstep of how much the triangle faces forward (0.22 to 0.62), times a soft elliptical mask in picture space, so the sides and back of the head, hands and everything else stay untouched.
4. The atlas is written back with `iwilib.write`.

`FACE_GAIN` (default 1.1 in `make-face.sh`) brightens the picture, because the game lighting is dark; 1.45 washed it out to white. `FACE_SAT` (1.35) boosts saturation. Expect a modest result: the atlas is low resolution and the head unwraps are small, the mesh has glowing eye surfaces (they cover the eyes) and short hair, so the result reads as a grey-ish zombie version of the picture, not a sharp likeness. Use `tools/dev/preview_heads.py ZT_RAW IWI OUT.png` for an offline render of the four heads with a texture.

### Making the face picture

`make-face.sh` wants a square, front-facing, evenly lit picture of a face filling the frame (hair at the top and sides, neck at the bottom, neutral expression, no shadows). A phone selfie will not do as it is. `tools/avatar_gen.py` makes one from a normal photo with an image-editing model on OpenRouter (about $0.14 per image, three takes are usually enough):

```
export OPENROUTER_API_KEY=...
python3 -P tools/avatar_gen.py front_human my_photo.jpg 3      # model: google/gemini-3-pro-image
```

`KIND` is `front_human` (a clean natural face, recommended: the game lighting already adds the zombie look), `front_zombie` (decayed skin, wounds, glowing eyes baked in) or `portrait` (a head-and-shoulders zombie picture, just for fun). The prompts are at the top of the script. They ask the model to use the photo only for identity (face shape, brow, nose, eyes, hair, facial hair), to ignore the photo's background, and to produce a flat, front-facing, evenly lit, symmetric image with no shadows. Look at the takes and pick the most frontal and symmetric one. Flaws to expect: slight perspective, a vignette, hair hiding the ears, baked-in wounds that are not symmetric.

`tools/prep_face_human.py IN.png OUT.png` removes the light studio background (colour distance from the corners plus a warm-colour test, feathered) and fills it with nearby hair and skin colour, so no white shows between curls. `make-face.sh` runs it unless `NO_PREP=1`.

Only use a photo of yourself or of someone who agreed. Do not commit it or the generated faces (the `.gitignore` excludes the usual places).

## 3. Checking that it worked

- `tools/verify_pack.py web kino --hash` must say `unusable 0` (`apply-mod.sh` runs it). It checks sizes and sha256 of every manifest entry.
- In game, a log line `browser sound miss ... side table miss` means the sounds.pack was built wrongly (see the rules above). No such lines means the clips were accepted.
- For an automated check, `tools/dev/play_session.py` drives a headless Chrome into the game, takes screenshots and records the audio of a PulseAudio null sink; `tools/stt.py` on the recording should hear your clip's words. The game mixes, reverbs and attenuates the voices, so a cross-correlation against the clip stays low; use speech-to-text as the proof.
- For a close-up of a zombie face, a test mod that places a zombie in front of the player is the easy way. This repo does not include one.

## 4. Other tools

| Tool | Use |
|---|---|
| `tools/fetch_map.py WEB SLUG` | mirror one map from the CDN, resumable (what `get-web-build.sh` uses to fill gaps) |
| `tools/verify_pack.py WEB MAP [--hash]` | check a map pack against its manifest |
| `tools/mkmod.py WEB MAP --file REL=LOCAL --replace REL=LOCAL` | add or replace pack files and rewrite the manifest |
| `tools/patch_playjs.py SRC DST MOD` | always-on mod list in `play.js` |
| `tools/ffraw.py IN.ff OUT.bin` | decompress a zone file |
| `tools/ksp.py` | inspect and rebuild `sounds.pack` |

Run Python tools as `python3 -P tool.py` (or `-I` for those that only use the standard library). `-P` keeps the current folder out of the import path and still lets numpy and Pillow load from your user site.
