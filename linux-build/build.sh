#!/usr/bin/env bash
# redactor-build-tools/linux-build/build.sh
#
# Builds one Redactor app's Linux executable via the shared toolchain
# image (Dockerfile in this same folder). The app's own repo is bind-
# mounted in at container-start, not baked into the image, so editing
# code never requires a Docker rebuild -- only this script's own
# `docker build` step (cached, near-instant once the image already
# exists) plus the app's own `pip install -r requirements.txt` (run
# fresh each time, inside the container, since it's cheap and keeps
# this correct even if requirements.txt just changed).
#
# Usage:
#   ./build.sh <path-to-app-repo> <spec-file-name> [--test]
#
# Examples:
#   ./build.sh /c/Dev/videoredactor videoredactor.spec
#   ./build.sh /c/Dev/mp3redactor mp3redactor.spec --test
#
# Output lands in <path-to-app-repo>/dist/, same layout as a normal
# Windows PyInstaller build -- just a Linux ELF binary instead of a
# .exe. Note: each .spec's icon="assets/icon.ico" is simply ignored by
# PyInstaller on Linux (icon embedding is a Windows/Mac-only concept),
# not an error -- fine for a first "does it build and run" pass; a
# real Linux release would want its own icon/.desktop-file packaging
# on top of this (see the redactor-family-cross-platform-port notes).

set -euo pipefail

IMAGE_NAME="redactor-linux-build"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <path-to-app-repo> <spec-file-name> [--test]" >&2
    exit 1
fi

REPO_PATH="$(cd "$1" && pwd)"
SPEC_FILE="$2"
RUN_TESTS="${3:-}"

echo "==> Building toolchain image ($IMAGE_NAME)..."
docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"

BUILD_CMD="pip install -r requirements.txt"
if [ "$RUN_TESTS" = "--test" ]; then
    BUILD_CMD="$BUILD_CMD && python3 -m pytest -q"
fi
BUILD_CMD="$BUILD_CMD && pyinstaller --noconfirm $SPEC_FILE"

echo "==> Building $SPEC_FILE against $REPO_PATH..."
# MSYS_NO_PATHCONV=1 stops Git Bash on Windows from "helpfully"
# reinterpreting the container-side /src path as a Windows path --
# without it, -v "$REPO_PATH:/src" can silently mangle into something
# like "C:/Program Files/Git/src", which is the single most common way
# this kind of docker command fails specifically from Git Bash.
MSYS_NO_PATHCONV=1 docker run --rm \
    -v "${REPO_PATH}:/src" \
    -w /src \
    "$IMAGE_NAME" \
    bash -c "$BUILD_CMD"

echo "==> Done. Output in ${REPO_PATH}/dist/"
