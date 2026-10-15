#!/usr/bin/env bash
# get-web-build.sh [MAP...] : download the browser build of the game into ./web (or $BO1Z_WEB).
# The build is the vel.gg web port as mirrored by UMMMM-GUYSSS/Call-of-Duty-Black-Ops-Zombies, pinned to the commit this repo was tested with.
# Only the site shell and the maps you ask for are fetched (default: kino, the map the voice/face mod targets; about 1.3 GB on disk).
# Other maps: kino five moon nacht verruckt shangrila shinonuma riese cotd ascension (each is similar size).
# If the mirror is missing files for a map (it was uploaded in pieces), the gaps are filled from the CDN with tools/fetch_map.py.
# None of this game data is part of this repository.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
need git "$PYTHON"
MAPS=("$@"); [ ${#MAPS[@]} -gt 0 ] || MAPS=(kino)
for m in "${MAPS[@]}"; do [ "$m" = five ] && die "map 'five' lives in the site root of the mirror; use tools/fetch_map.py \"\$BO1Z_WEB\" five"; done

if [ ! -d "$BO1Z_WEB/.git" ] && [ ! -f "$BO1Z_WEB/.git" ]; then
  [ -z "$(ls -A "$BO1Z_WEB" 2>/dev/null)" ] || die "$BO1Z_WEB exists and is not a clone made by this script"
  mkdir -p "$(dirname "$BO1Z_WEB")"
  echo "Cloning the site shell (no map data yet)..."
  git clone --quiet --filter=blob:none --no-checkout "$BO1Z_WEB_REPO" "$BO1Z_WEB"
fi
cd "$BO1Z_WEB"
git sparse-checkout init --no-cone >/dev/null 2>&1 || true
PATTERNS=('/*' '!/*/')     # every top-level file, no directories ...
for m in "${MAPS[@]}"; do PATTERNS+=("/$m/"); done   # ... plus the maps you asked for
git sparse-checkout set --no-cone "${PATTERNS[@]}"
echo "Checking out ${MAPS[*]} at $BO1Z_WEB_COMMIT (this downloads the map data)..."
git checkout --quiet "$BO1Z_WEB_COMMIT"

status=0
for m in "${MAPS[@]}"; do
  echo "Verifying $m ..."
  if ! "$PYTHON" -I "$BO1Z_ROOT/tools/verify_pack.py" "$BO1Z_WEB" "$m"; then
    echo "Filling the gaps for $m from the CDN ..."
    "$PYTHON" -I "$BO1Z_ROOT/tools/fetch_map.py" "$BO1Z_WEB" "$m"
    "$PYTHON" -I "$BO1Z_ROOT/tools/verify_pack.py" "$BO1Z_WEB" "$m" --hash || status=1
  fi
done
[ $status -eq 0 ] && echo "Done. Next: scripts/make-cert.sh" || die "some files are still missing or wrong; re-run the script"
