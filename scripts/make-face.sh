#!/usr/bin/env bash
# make-face.sh FACE.png : bake a front-facing face picture onto the Kino zombie head texture (c_ger_zombie_head1_c) and write work/mod/c_ger_zombie_head1_c.iwi.
# FACE.png: square, front-facing, evenly lit face filling the frame (tools/avatar_gen.py can make one from a photo; see docs/MODDING.md).
# Env: NO_PREP=1 skips the background removal (use it if your picture already fills the frame edge to edge); FACE_GAIN (default 1.1) brightens, FACE_SAT (default 1.35) saturates.
# Needs python3 -P with numpy and Pillow. Then run scripts/apply-mod.sh.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
need "$PYTHON"
FACE=${1:-}; [ -f "$FACE" ] || die "usage: make-face.sh FACE.png"
backup_originals
PACK="$BO1Z_WEB/kino/pack"; Z="$PACK/zone/Common/zombie_theater.ff"; W="$BO1Z_WORK"
mkdir -p "$W/mod"
if [ ! -f "$W/zombie_theater.raw" ]; then
  if [ -d "$Z.part" ]; then      # split into 8 MiB pieces named 0,1,2 ...: join them in NUMERIC order
    n=$(ls "$Z.part" | wc -l); : > "$W/zombie_theater.ff"
    for ((i = 0; i < n; i++)); do cat "$Z.part/$i" >> "$W/zombie_theater.ff"; done
    "$PYTHON" -I "$BO1Z_ROOT/tools/ffraw.py" "$W/zombie_theater.ff" "$W/zombie_theater.raw"; rm -f "$W/zombie_theater.ff"
  elif [ -f "$Z" ]; then "$PYTHON" -I "$BO1Z_ROOT/tools/ffraw.py" "$Z" "$W/zombie_theater.raw"
  else die "zombie_theater.ff not found under $PACK/zone/Common"; fi
fi
[ -f "$W/head_orig.iwi" ] || "$PYTHON" -I "$BO1Z_ROOT/tools/extract_head.py" "$PACK/main" "$W/head_orig.iwi"
SRC=$FACE
if [ -z "${NO_PREP:-}" ]; then "$PYTHON" -P "$BO1Z_ROOT/tools/prep_face_human.py" "$FACE" "$W/face_prepped.png"; SRC="$W/face_prepped.png"; fi
FACE_GAIN=${FACE_GAIN:-1.1} FACE_SAT=${FACE_SAT:-1.35} "$PYTHON" -P "$BO1Z_ROOT/tools/bake_face.py" "$W/zombie_theater.raw" "$W/head_orig.iwi" "$SRC" "$W/mod/c_ger_zombie_head1_c.iwi"
echo "Next: scripts/apply-mod.sh"
