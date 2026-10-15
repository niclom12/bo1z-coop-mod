#!/usr/bin/env bash
# make-voices.sh [CLIP_A [CLIP_B]] : build a modded Kino sounds.pack where every living zombie vocal plays one of two clips (A on even variants, B on odd).
# Defaults to the two example clips in examples/voices. Use your own: any wav/mp3/opus, about 1 to 2 seconds each (see docs/MODDING.md for how to generate them).
# Reads the untouched pack from the backup (made on first use) and writes work/mod/kino-sounds.pack. Then run scripts/apply-mod.sh.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
need ffmpeg ffprobe "$PYTHON"
A=${1:-$BO1Z_ROOT/examples/voices/emdash_man.wav}; B=${2:-$BO1Z_ROOT/examples/voices/hi_johan_girl.wav}
backup_originals
mkdir -p "$BO1Z_WORK/mod"
"$PYTHON" -I "$BO1Z_ROOT/tools/mk_zvoices.py" "$BO1Z_BACKUP/sounds.pack" "$BO1Z_WORK/mod/kino-sounds.pack" "$A" "$B"
echo "Wrote $BO1Z_WORK/mod/kino-sounds.pack. Next: scripts/apply-mod.sh"
