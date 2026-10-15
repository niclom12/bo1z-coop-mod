#!/usr/bin/env bash
# make-cert.sh : create a self-signed TLS certificate for your LAN IP, in ./certs (or $BO1Z_CERTS). Used by the game server and the relay.
# The game needs a secure context (https) when it is not opened on localhost, and Chrome only accepts the relay's wss:// over a cert it trusts for that
# address, so the certificate carries the LAN IP as a subject alternative name. Re-run it if your LAN IP changes (BO1Z_LAN_IP=1.2.3.4 to force one).
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
need openssl
IP=$(detect_lan_ip)
mkdir -p "$BO1Z_CERTS"
if [ -f "$BO1Z_CERTS/cert.pem" ] && [ -z "${FORCE:-}" ] && openssl x509 -in "$BO1Z_CERTS/cert.pem" -noout -ext subjectAltName 2>/dev/null | grep -q "IP Address:$IP"; then
  echo "Certificate for $IP already exists in $BO1Z_CERTS (FORCE=1 to recreate)."; exit 0
fi
openssl req -x509 -newkey rsa:2048 -nodes -days 825 -subj "/CN=$IP" \
  -addext "subjectAltName=IP:$IP,IP:127.0.0.1,DNS:localhost" \
  -keyout "$BO1Z_CERTS/key.pem" -out "$BO1Z_CERTS/cert.pem" 2>/dev/null
chmod 600 "$BO1Z_CERTS/key.pem"
echo "Wrote $BO1Z_CERTS/cert.pem and key.pem for $IP (valid 825 days). Keep key.pem private."
