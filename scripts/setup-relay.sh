#!/usr/bin/env bash
# setup-relay.sh : prepare your own co-op relay (a Cloudflare Worker run locally by wrangler) in ./work/relay.
# Why: the shared relay of the extension runs on Cloudflare's free plan and stops with error 1027 when its daily quota is used up. Running the same worker on
# your own machine has no quota and the lowest possible ping on a LAN.
# It downloads AllanLotta/bo1-zombies-coop at the pinned version, copies its relay/ folder, allows this site's origins, and installs wrangler with npm.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
need git node npm patch
ensure_coop_upstream
R="$BO1Z_WORK/relay"
rm -rf "$R"; cp -R "$BO1Z_WORK/coop-upstream/relay" "$R"
render "$BO1Z_ROOT/patches/relay-wrangler.patch.in" | patch -p1 -d "$R" >/dev/null
echo "Installing wrangler (npm) ..."
(cd "$R" && npm install --no-audit --no-fund --loglevel=error)
echo "Relay ready in $R. Start it with scripts/run-relay.sh"
