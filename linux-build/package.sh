#!/usr/bin/env bash
# redactor-build-tools/linux-build/package.sh
#
# Packages a Linux build made by build.sh into the release download:
#   <repo>/dist-linux/<app>-linux-x86_64.tar.gz
# holding <app>/<app> (the single-file executable, exec bit kept -- the
# reason for a tarball rather than the bare binary: a browser download
# loses it) and <app>/README-LINUX.txt.
#
# Usage:
#   ./package.sh <path-to-app-repo> <app-name> "<display name>"
# Example:
#   ./package.sh /c/Dev/cbzredactor cbzredactor "The ƆBZ Redactor"

set -euo pipefail

if [ $# -lt 3 ]; then
    echo "Usage: $0 <path-to-app-repo> <app-name> \"<display name>\"" >&2
    exit 1
fi

REPO_PATH="$(cd "$1" && pwd)"
APP="$2"
DISPLAY_NAME="$3"
DIST="$REPO_PATH/dist-linux"
STAGE="$DIST/package/$APP"

if [ ! -f "$DIST/$APP" ]; then
    echo "No Linux build at $DIST/$APP -- run build.sh first." >&2
    exit 1
fi

rm -rf "$DIST/package"
mkdir -p "$STAGE"
cp "$DIST/$APP" "$STAGE/$APP"
chmod 755 "$STAGE/$APP"
cat > "$STAGE/README-LINUX.txt" <<EOF
$DISPLAY_NAME for Linux (x86_64)

Start it:
    tar xzf $APP-linux-x86_64.tar.gz
    ./$APP/$APP

It's a single self-contained program: Python and Qt are inside, nothing
to install. Put it wherever you like (e.g. ~/.local/bin).

Needs a 64-bit desktop Linux with glibc 2.35 or newer: Ubuntu 22.04+,
Debian 12+, Fedora 36+, Linux Mint 21+ and the like.

If it doesn't start, run it from a terminal to see why, and please
report what it says.

Settings are kept in ~/.config/$APP/.
External tools the app can use are found on your PATH.
EOF

# Modes and owner set explicitly: packed on Windows (Docker Desktop's
# bind mount) the files carry no exec bit at all.
TARBALL="$DIST/$APP-linux-x86_64.tar"
rm -f "$TARBALL" "$TARBALL.gz"
TAR_OPTS=(--owner=0 --group=0 --numeric-owner --no-recursion -C "$DIST/package")
tar -cf "$TARBALL" "${TAR_OPTS[@]}" --mode=755 "$APP" "$APP/$APP"
tar -rf "$TARBALL" "${TAR_OPTS[@]}" --mode=644 "$APP/README-LINUX.txt"
gzip -9 "$TARBALL"
rm -rf "$DIST/package"
echo "==> $DIST/$APP-linux-x86_64.tar.gz"
