#!/usr/bin/env bash
# serve.sh : run the game server (https on $BO1Z_PORT, default 20100, plus plain http on 127.0.0.1:$BO1Z_HTTP_PORT, default 20101).
# Open https://<your-LAN-IP>:20100/bo1z/ . The server sets the COOP/COEP headers the engine needs and never caches code or manifests.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
need node
[ -f "$BO1Z_WEB/index.html" ] || die "no game site in $BO1Z_WEB; run scripts/get-web-build.sh"
[ -f "$BO1Z_CERTS/cert.pem" ] || die "no certificate in $BO1Z_CERTS; run scripts/make-cert.sh"
echo "Game:   https://$(detect_lan_ip):$BO1Z_PORT/bo1z/"
exec node "$BO1Z_ROOT/tools/bo1z-serve.mjs" --root "$BO1Z_WEB" --host 0.0.0.0 --port "$BO1Z_PORT" --http-port "$BO1Z_HTTP_PORT" \
  --path /bo1z/ --cert "$BO1Z_CERTS/cert.pem" --key "$BO1Z_CERTS/key.pem" "$@"
