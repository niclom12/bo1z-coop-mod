#!/usr/bin/env bash
# install-systemd.sh : install user services bo1z-web (game server) and bo1z-relay from systemd/*.template, so they run in the background.
# Linux with systemd only. They are not enabled at boot: start/stop with  systemctl --user start|stop bo1z-web bo1z-relay
# Run after get-web-build.sh, make-cert.sh and setup-relay.sh.
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
need systemctl
D="$HOME/.config/systemd/user"; mkdir -p "$D"
for s in bo1z-web bo1z-relay; do render "$BO1Z_ROOT/systemd/$s.service.template" > "$D/$s.service"; done
systemctl --user daemon-reload
echo "Installed $D/bo1z-web.service and bo1z-relay.service. Start them with: systemctl --user start bo1z-web bo1z-relay"
