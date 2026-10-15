#!/usr/bin/env bash
# patch-extension.sh [OUT_DIR] : build the co-op Chrome extension that works with your own server.
# Downloads AllanLotta/bo1-zombies-coop v2.1.1 (commit 728d51e), copies its extension/ folder and applies patches/coop-extension.patch.in, which only adds your
# LAN address and the local ports to the extension's content-script match list. The extension code itself is not changed and is not stored in this repo
# (the upstream project has no licence). Default output: ./build/coop-extension. Load it in Chrome: chrome://extensions -> Developer mode -> Load unpacked.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
need git patch
OUT=${1:-$BO1Z_BUILD/coop-extension}
ensure_coop_upstream
rm -rf "$OUT"; mkdir -p "$(dirname "$OUT")"; cp -R "$BO1Z_WORK/coop-upstream/extension" "$OUT"
render "$BO1Z_ROOT/patches/coop-extension.patch.in" | patch -p1 -d "$OUT" >/dev/null
echo "Built $OUT"
grep -A5 '"matches"' "$OUT/manifest.json" | sed 's/^/  /'
echo "Load it: chrome://extensions -> Developer mode -> Load unpacked -> $OUT (do this on every player's computer)."
