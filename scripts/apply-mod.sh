#!/usr/bin/env bash
# apply-mod.sh : put the modded files from work/mod into the Kino pack of the game site and update its manifest, so browsers re-download exactly those files.
#   work/mod/kino-sounds.pack            (from make-voices.sh)  replaces web/sound/sounds.pack
#   work/mod/c_ger_zombie_head1_c.iwi    (from make-face.sh)    added as mods/zcustom/images/..., and play.js is patched to always load the zcustom mod
# Either part may be missing; only what exists is applied. The untouched originals are kept in web/.bo1z-backup; scripts/restore.sh puts them back.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
need "$PYTHON"
M="$BO1Z_WORK/mod"; ARGS=(); done_any=
backup_originals
if [ -f "$M/c_ger_zombie_head1_c.iwi" ]; then
  "$PYTHON" -I "$BO1Z_ROOT/tools/patch_playjs.py" "$BO1Z_BACKUP/play.js" "$BO1Z_WEB/play.js.new" zcustom
  mv "$BO1Z_WEB/play.js.new" "$BO1Z_WEB/play.js"
  ARGS+=(--file "mods/zcustom/images/c_ger_zombie_head1_c.iwi=$M/c_ger_zombie_head1_c.iwi"); done_any=1
fi
[ -f "$M/kino-sounds.pack" ] && { ARGS+=(--replace "web/sound/sounds.pack=$M/kino-sounds.pack"); done_any=1; }
[ -n "$done_any" ] || die "nothing to apply: run scripts/make-voices.sh and/or scripts/make-face.sh first"
"$PYTHON" -I "$BO1Z_ROOT/tools/mkmod.py" "$BO1Z_WEB" kino "${ARGS[@]}"
"$PYTHON" -I "$BO1Z_ROOT/tools/verify_pack.py" "$BO1Z_WEB" kino --hash
echo "Applied. Players: reload the page; the downloader fetches only the changed files. If a browser keeps old data, clear the site data for the origin (see README, Troubleshooting)."
