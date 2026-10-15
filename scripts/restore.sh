#!/usr/bin/env bash
# restore.sh : undo apply-mod.sh. Puts back the untouched play.js, Kino manifest and sounds.pack from web/.bo1z-backup and removes the zcustom mod.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
[ -f "$BO1Z_BACKUP/play.js" ] || die "no backup in $BO1Z_BACKUP: nothing was applied, or it was removed"
cp "$BO1Z_BACKUP/play.js" "$BO1Z_WEB/play.js"
cp "$BO1Z_BACKUP/kino-manifest.json" "$BO1Z_WEB/kino/manifest.json"
cp "$BO1Z_BACKUP/sounds.pack" "$BO1Z_WEB/kino/pack/web/sound/sounds.pack"
[ -f "$BO1Z_BACKUP/sounds.pack.kop" ] && cp "$BO1Z_BACKUP/sounds.pack.kop" "$BO1Z_WEB/kino/pack/web/sound/sounds.pack.kop"
rm -rf "$BO1Z_WEB/kino/pack/mods/zcustom"; rmdir "$BO1Z_WEB/kino/pack/mods" 2>/dev/null || true
"$PYTHON" -I "$BO1Z_ROOT/tools/verify_pack.py" "$BO1Z_WEB" kino --hash
echo "Restored the retail Kino pack."
