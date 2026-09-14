# redactor-build-tools/linux-build/Dockerfile
#
# Shared Linux build toolchain for the whole Redactor family
# (cbzredactor, epubredactor, mp3redactor, videoredactor) -- one image,
# reused for all four, since the toolchain itself (Python + PyInstaller
# + the system libraries PyQt6's bundled Qt needs at runtime) is
# identical across all of them. Only each app's own requirements.txt
# and .spec file differ, and those come in via a bind mount at
# `docker run` time (see build.sh) -- never baked into this image, so
# editing app code never requires rebuilding it.
#
# Base pinned to Ubuntu 22.04 (glibc 2.35) rather than whatever's
# newest: glibc is forward-compatible only, so a binary built on a
# newer base won't run on an older user's system. 22.04 is a
# deliberate middle ground -- covers effectively every Linux desktop
# still in real use as of 2026 (Ubuntu 22.04+, Debian 12+, Fedora 36+,
# Mint 21+, ...) without pinning to something already past its own
# support window. For maximum compatibility at the cost of a couple
# years of headroom, swap this to ubuntu:20.04 instead.
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    QT_QPA_PLATFORM=offscreen

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv \
        build-essential \
        git \
        # PyQt6's bundled Qt still needs these system libraries at
        # runtime -- without them, even a headless/offscreen
        # QApplication() fails to construct, which matters both for
        # `pyinstaller` itself (it imports the app's modules to trace
        # dependencies) and for running the test suite in-container.
        libxcb-cursor0 libxcb-xinerama0 libxkbcommon-x11-0 \
        libgl1 libegl1 libdbus-1-3 \
        fontconfig \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip pyinstaller

WORKDIR /src
# Deliberately no COPY of app source here -- see build.sh, which bind-
# mounts the actual repo in at container-start instead.
