#!/usr/bin/env python3
"""patch_playjs.py SRC_PLAY_JS DST_PLAY_JS MOD[,MOD...] : write DST = SRC with an always-on mod list. For each MOD that the loaded map pack ships
(manifest paths mods/<MOD>/...), the engine is started with it in fs_mods, whatever the Options checkboxes say (no UI for it).
SRC is the untouched play.js (apply-mod.sh keeps a copy in web/.bo1z-backup/). Idempotent: patches SRC, never DST in place."""
import sys
src, dst, mods = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
s = open(src).read()
old = "chosen.mods = chosen.mods.filter(name => shipped.includes(name)); state.mods = chosen.mods;"
assert s.count(old) == 1, 'anchor not found'
new = ("chosen.mods = chosen.mods.filter(name => shipped.includes(name));\n"
       "  // bo1z-coop-mod: always-on mods (images/sounds override); only when this map's pack ships them\n"
       f"  for (const name of {mods!r}) if (state.manifest?.files?.some(f => f.path.toLowerCase().startsWith(`mods/${{name}}/`)) && !chosen.mods.includes(name)) chosen.mods.push(name);\n"
       "  state.mods = chosen.mods;")
open(dst, 'w').write(s.replace(old, new))
print('patched', dst, 'forced mods', mods)
