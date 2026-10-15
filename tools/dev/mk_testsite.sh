#!/bin/sh
# mk_testsite.sh SRC_WEB DEST_TEST : symlink farm of the site (no data copied) so experiments never touch SRC_WEB.
set -e
rm -rf "$2"; mkdir -p "$2"
for e in "$1"/*; do n=$(basename "$e"); cp -rs "$(readlink -f "$e")" "$2/$n"; done
