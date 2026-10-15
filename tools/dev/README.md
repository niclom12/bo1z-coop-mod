# tools/dev

Helpers used while building and testing the mod. Not needed to play. Run them with `python3 -P`.

- `hl.py`, `game.py`, `play_session.py`, `coop_session.py`, `opfs_ls.py`: drive a headless Chrome over the DevTools protocol (needs `pip install websockets` and `CHROME=/path/to/chrome`) to load the game, take screenshots, record audio and run a host plus a guest through the relay.
- `preview_heads.py`, `render_mesh.py`, `xsurf.py`, `scanverts.py`, `iwi_tint.py`: offline checks of the head meshes and textures (mesh finders, a tiny software renderer, a recolour proof of concept).
- `rawfiles.py`, `fetch_horde.py`, `find_clip.py`, `mk_testsite.sh`: odds and ends (extract script text from a decompressed zone file, fetch the "Hell mode" overlay, cross-correlate a clip against a recording, make a symlink copy of a site for experiments).
