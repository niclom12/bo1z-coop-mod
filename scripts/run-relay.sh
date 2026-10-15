#!/usr/bin/env bash
# run-relay.sh : run the local co-op relay over https on 0.0.0.0:$BO1Z_RELAY_PORT (default 20000), using the certificate from make-cert.sh.
# Players set their relay to https://<your-LAN-IP>:20000 in the extension's Co-op Settings.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
R="$BO1Z_WORK/relay"
[ -x "$R/node_modules/.bin/wrangler" ] || die "relay not set up; run scripts/setup-relay.sh"
[ -f "$BO1Z_CERTS/cert.pem" ] || die "no certificate in $BO1Z_CERTS; run scripts/make-cert.sh"
echo "Relay:  https://$(detect_lan_ip):$BO1Z_RELAY_PORT   (health check: /health)"
cd "$R"
export WRANGLER_SEND_METRICS=false CI=1
exec ./node_modules/.bin/wrangler dev --port "$BO1Z_RELAY_PORT" --ip 0.0.0.0 --local --local-protocol https \
  --https-key-path "$BO1Z_CERTS/key.pem" --https-cert-path "$BO1Z_CERTS/cert.pem" --show-interactive-dev-session=false "$@"
