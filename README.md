# BO1 Zombies web co-op: self-hosted setup and voice/face mod tools

Host your own four-player Call of Duty: Black Ops Zombies game for friends on your home network, in the browser, with no shared server and no quota. This repo has the scripts that set it up, plus tools to swap the zombie voices and the zombie face for your own.

## What this is, and what it is not

This is a fan project. It is **not affiliated with, endorsed by or sponsored by Activision, Treyarch or vel.gg**. Call of Duty and Black Ops are trademarks of Activision.

**Nothing copyrighted is in this repository.** No game files, no game sounds or textures, no engine code, and none of the code from the projects below. The scripts download those from their public sources when you run them. You need the game data from the web build to play, and you are responsible for having the right to use it.

It builds on three things you download separately:

| Piece | Source | Pinned to |
|---|---|---|
| Browser build of the game (site shell and map data) | [UMMMM-GUYSSS/Call-of-Duty-Black-Ops-Zombies](https://github.com/UMMMM-GUYSSS/Call-of-Duty-Black-Ops-Zombies), a mirror of the vel.gg web port | commit `8c4d40a` |
| Co-op Chrome extension and relay | [AllanLotta/bo1-zombies-coop](https://github.com/AllanLotta/bo1-zombies-coop) (no licence, so not copied here; we ship a small patch and a script that applies it) | tag `v2.1.1`, commit `728d51e` |
| This repo | scripts, a static file server, mod tools | MIT |

The MIT licence covers **only the code written for this repo** (see `LICENSE`). It says nothing about the game, the web port, the extension or the relay.

## What you get

- `scripts/`: one script per step, below.
- `tools/bo1z-serve.mjs`: a small static server for the game (HTTPS, the cross-origin isolation headers the engine needs, HTTP range requests, no caching of code).
- `patches/`: the changes to the co-op extension (it must also run on your own address) and to the relay (it must accept your site's origin).
- `tools/` and `docs/MODDING.md`: tools and notes for replacing the zombie voices and the zombie face on the Kino der Toten map.
- `examples/voices/`: two short text-to-speech clips, used as the default voices.

## Requirements

- Linux or macOS (the scripts are bash). Windows: use WSL.
- `git`, `node` 18 or newer, `npm`, `openssl`, `patch`, `curl`
- `python3` 3.11 or newer with `numpy` and `Pillow` (`pip install numpy Pillow`), only for the mod tools
- `ffmpeg` and `ffprobe`, only for the voice tool
- Google Chrome (or another Chromium browser) on every player's computer, with a decent GPU: the engine uses WebGPU
- About 1.5 GB of free disk for the Kino map (other maps are similar in size)
- All players on the same Wi-Fi or LAN

## Quick start

Run everything from the root of this repo. Steps 1 to 5 are done once, on the machine that will host the game server.

**1. Get the web build.**

```
scripts/get-web-build.sh
```

This downloads the site shell and the Kino der Toten map into `./web` (about 760 MB, plus about 540 MB of git objects, so 1.3 GB of disk). Add map names to get more, for example `scripts/get-web-build.sh kino moon`. If the mirror is missing some files, the script fills the gaps from the CDN and checks every file.

**2. Make a certificate for your LAN address.**

```
scripts/make-cert.sh
```

The game only starts in a secure context, and the co-op relay needs `wss://`, so the server uses HTTPS. The script detects your LAN IP (for example `192.168.1.20`; set `BO1Z_LAN_IP=...` if it guesses wrong) and creates a self-signed certificate valid for that address in `./certs`. The browser will show a warning for it once per player (step 6).

**3. Start the game server.**

```
scripts/serve.sh
```

It prints the address, `https://<your-LAN-IP>:20100/bo1z/`. Leave it running. To run it in the background on Linux with systemd, use `scripts/install-systemd.sh` instead and then `systemctl --user start bo1z-web`.

**4. Set up and start the relay.**

The relay passes game packets between the host and the guests. The extension's default relay is a shared one on Cloudflare's free plan, and it stops with **error 1027** when its daily quota runs out. Running the same relay yourself has no quota. Two commands:

```
scripts/setup-relay.sh      # downloads the relay at the pinned version, allows your origin, runs npm install
scripts/run-relay.sh        # https on 0.0.0.0:20000
```

(`systemctl --user start bo1z-relay` also works after `install-systemd.sh`.) Check it from the host: `curl -k https://<your-LAN-IP>:20000/health` should answer `{"ok":true,...}`.

**5. Build the co-op extension and load it in Chrome.**

```
scripts/patch-extension.sh
```

This downloads the extension at the pinned version and applies our patch, which adds your LAN address and the local ports to the pages it runs on. The result is in `./build/coop-extension`. Copy that folder to every player's computer, then in Chrome open `chrome://extensions`, switch on **Developer mode**, click **Load unpacked** and pick the folder.

**6. Each player: join.**

1. Open `https://<LAN-IP>:20100/bo1z/` and accept the certificate warning (Advanced, Proceed).
2. In another tab open `https://<LAN-IP>:20000/health` and accept the warning there too. Without this the page cannot open the relay's WebSocket.
3. Back on the game page open the extension's **Co-op Settings**, choose **Change relay**, enter `https://<LAN-IP>:20000` and save. Everyone must use the same relay.
4. The host starts a lobby for Kino der Toten; the friends join with the invite link or room code.

The first load downloads the map into the browser's storage (a few hundred MB, only once; later loads fetch just what changed).

### Firewall

Allow your LAN to reach the two HTTPS ports, and nothing else. With ufw (use your own subnet):

```
sudo ufw allow from 192.168.1.0/24 to any port 20100 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 20000 proto tcp
```

Port 20101 (plain HTTP) listens on 127.0.0.1 only. All three ports can be changed with `BO1Z_PORT`, `BO1Z_HTTP_PORT` and `BO1Z_RELAY_PORT`; if you change them, rebuild the extension (step 5) and re-run `setup-relay.sh`.

## Custom zombie voices and face (optional)

```
scripts/make-voices.sh                 # the example clips; or: make-voices.sh my_a.wav my_b.wav
scripts/make-face.sh my_face.png       # a front-facing, evenly lit face picture
scripts/apply-mod.sh                   # writes into ./web and updates the manifest
scripts/restore.sh                     # back to retail
```

Players only need to reload the page: the downloader notices the new manifest and fetches the two changed files. `docs/MODDING.md` explains how it works, how to make your own clips and face texture, and the format details. The mod covers Kino der Toten only.

## Troubleshooting

- **The browser keeps old files / my mod does not show.** The server never caches code or manifests, but the game stores its data in the browser (OPFS). Reload with Ctrl+Shift+R first. If that is not enough: DevTools (F12), Application, Storage, tick everything including "Cache storage" and OPFS-backed storage, **Clear site data** for that origin, then reload. A fresh profile downloads everything again.
- **Certificate warning every time, or "connection failed" to the relay.** Each address needs its own accepted warning: the game page (`:20100`) and the relay (`:20000`). If your LAN IP changed, the certificate no longer matches it: `FORCE=1 scripts/make-cert.sh`, restart both servers, rebuild the extension (`patch-extension.sh`), re-run `setup-relay.sh`, reload the extension in `chrome://extensions`, and tell players the new address.
- **The co-op panel does not appear.** The extension only runs on the origins in its match list: `https://<LAN-IP>:20100`, `http://127.0.0.1:20101`, `http://localhost:20101` and `vel.gg`. `https://localhost:20100` is **not** matched. Use the LAN address (also on the host machine), or `http://localhost:20101` for solo tests on the host.
- **"Error 1027" or "this relay used up today's free allowance".** You are still on the shared relay. Set the relay to your own address (step 6, item 3).
- **Black screen or "WebGPU not available".** Use a recent desktop Chrome and check `chrome://gpu`. Remote desktop sessions and some VMs have no WebGPU.
- **`get-web-build.sh` says files are missing.** Re-run it; it is resumable. The verification step prints which files are wrong.
- **The relay says the origin is not allowed.** `setup-relay.sh` writes your origins into the relay's config. If you changed the address or ports, run it again.

## Layout

```
scripts/     the steps above (lib.sh holds the shared settings and the pinned upstream versions)
tools/       server and mod tools (python3 -P ...); tools/dev has test helpers
patches/     templates of the changes to the extension and relay (@LAN_IP@ etc. are filled in by the scripts)
systemd/     user service templates
examples/    two example voice clips
docs/        MODDING.md
```

Settings you can override with environment variables: `BO1Z_WEB`, `BO1Z_WORK`, `BO1Z_CERTS`, `BO1Z_BUILD`, `BO1Z_PORT`, `BO1Z_HTTP_PORT`, `BO1Z_RELAY_PORT`, `BO1Z_LAN_IP`, `PYTHON`.
