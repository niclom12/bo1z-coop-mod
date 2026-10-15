# Shared settings for the scripts in this folder. Source it: . "$(dirname "$0")/lib.sh"
# Everything can be overridden with environment variables.

BO1Z_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
BO1Z_WEB=${BO1Z_WEB:-$BO1Z_ROOT/web}              # the game site (downloaded by get-web-build.sh)
BO1Z_WORK=${BO1Z_WORK:-$BO1Z_ROOT/work}           # scratch space and upstream clones
BO1Z_CERTS=${BO1Z_CERTS:-$BO1Z_ROOT/certs}        # cert.pem + key.pem (make-cert.sh)
BO1Z_BUILD=${BO1Z_BUILD:-$BO1Z_ROOT/build}        # patched extension output
BO1Z_PORT=${BO1Z_PORT:-20100}                     # game server, https
BO1Z_HTTP_PORT=${BO1Z_HTTP_PORT:-20101}           # game server, plain http on 127.0.0.1 only (localhost testing)
BO1Z_RELAY_PORT=${BO1Z_RELAY_PORT:-20000}         # co-op relay, https
PYTHON=${PYTHON:-python3}

# Upstream projects we build on. Neither is part of this repo; the scripts download them at these exact versions.
BO1Z_WEB_REPO=https://github.com/UMMMM-GUYSSS/Call-of-Duty-Black-Ops-Zombies.git
BO1Z_WEB_COMMIT=8c4d40ad6034dd8df42f383a757b602f900cdf9b      # main as of 2026-10-11 (the version this mod was built and tested on)
BO1Z_COOP_REPO=https://github.com/AllanLotta/bo1-zombies-coop.git
BO1Z_COOP_TAG=v2.1.1
BO1Z_COOP_COMMIT=728d51ec222a84ee5e30a564cba7ef03692769f7      # v2.1.1; later releases target a newer vel.gg engine than the web build above

die() { echo "error: $*" >&2; exit 1; }
need() { for c in "$@"; do command -v "$c" >/dev/null 2>&1 || die "'$c' is required but not installed"; done; }

# The machine's LAN address: BO1Z_LAN_IP if set, else the address used for the default route (Linux) or en0/en1 (macOS).
detect_lan_ip() {
  if [ -n "${BO1Z_LAN_IP:-}" ]; then echo "$BO1Z_LAN_IP"; return; fi
  local ip=""
  if command -v ip >/dev/null 2>&1; then ip=$(ip -4 route get 1.1.1.1 2>/dev/null | sed -n 's/.* src \([0-9.]*\).*/\1/p' | head -n1); fi
  if [ -z "$ip" ] && command -v ipconfig >/dev/null 2>&1; then ip=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true); fi
  [ -n "$ip" ] || die "could not detect your LAN IP; set BO1Z_LAN_IP=192.168.x.y"
  echo "$ip"
}

# Fill the @LAN_IP@ / @PORT@ / @HTTP_PORT@ / @RELAY_PORT@ / @REPO@ placeholders of a template file; result on stdout.
render() {
  sed -e "s|@LAN_IP@|$(detect_lan_ip)|g" -e "s|@PORT@|$BO1Z_PORT|g" -e "s|@HTTP_PORT@|$BO1Z_HTTP_PORT|g" \
      -e "s|@RELAY_PORT@|$BO1Z_RELAY_PORT|g" -e "s|@REPO@|$BO1Z_ROOT|g" -e "s|@CERTS@|$BO1Z_CERTS|g" -e "s|@WEB@|$BO1Z_WEB|g" -e "s|@WORK@|$BO1Z_WORK|g" "$1"
}

# Clone AllanLotta/bo1-zombies-coop at the pinned commit into $BO1Z_WORK/coop-upstream (once). Not redistributed: it stays in the git-ignored work folder.
ensure_coop_upstream() {
  need git
  local d="$BO1Z_WORK/coop-upstream"
  if [ ! -d "$d/.git" ]; then
    mkdir -p "$BO1Z_WORK"; git clone --quiet "$BO1Z_COOP_REPO" "$d" || die "could not clone $BO1Z_COOP_REPO"
  fi
  git -C "$d" fetch --quiet --tags 2>/dev/null || true
  git -C "$d" checkout --quiet --detach "$BO1Z_COOP_COMMIT" || die "commit $BO1Z_COOP_COMMIT ($BO1Z_COOP_TAG) not found in $d"
  [ "$(git -C "$d" rev-parse HEAD)" = "$BO1Z_COOP_COMMIT" ] || die "unexpected upstream commit"
}

# Save the untouched files that apply-mod.sh changes, once, so restore.sh can bring them back.
BO1Z_BACKUP=${BO1Z_BACKUP:-$BO1Z_WEB/.bo1z-backup}
backup_originals() {
  [ -f "$BO1Z_WEB/play.js" ] || die "no game site in $BO1Z_WEB; run scripts/get-web-build.sh first"
  mkdir -p "$BO1Z_BACKUP"
  [ -f "$BO1Z_BACKUP/play.js" ] || cp "$BO1Z_WEB/play.js" "$BO1Z_BACKUP/play.js"
  [ -f "$BO1Z_BACKUP/kino-manifest.json" ] || cp "$BO1Z_WEB/kino/manifest.json" "$BO1Z_BACKUP/kino-manifest.json"
  [ -f "$BO1Z_BACKUP/sounds.pack" ] || cp "$BO1Z_WEB/kino/pack/web/sound/sounds.pack" "$BO1Z_BACKUP/sounds.pack"
  if [ ! -f "$BO1Z_BACKUP/sounds.pack.kop" ] && [ -f "$BO1Z_WEB/kino/pack/web/sound/sounds.pack.kop" ]; then
    cp "$BO1Z_WEB/kino/pack/web/sound/sounds.pack.kop" "$BO1Z_BACKUP/sounds.pack.kop"
  fi
  return 0
}
