# redactor-build-tools

Cross-machine build tooling for the "Redactor" family (cbzredactor,
epubredactor, mp3redactor, videoredactor — see
[erlbon.github.io](https://erlbon.github.io) and each app's own repo).

Split out from `C:\Dev\_shared-tools` deliberately: that folder holds
genuinely machine-local setup (a manually-placed `upx.exe` binary,
release scripts with local absolute paths) that has no business in git.
This repo holds the opposite — small, portable, plain-text tooling with
no reason to be copied by hand between machines.

## `linux-build/`

Docker-based toolchain for building a Linux executable of any of the
four apps, from Windows (or anywhere with Docker), without needing a
physical Linux machine. See [[redactor-family-cross-platform-port]] in
project memory for the fuller Linux/Mac porting context this exists
for — this repo is the concrete first piece of that, since Linux is
the cheapest platform to start with (no code-signing tax, no hardware
purchase, and `WSL2`/Docker on Windows already provide a real Linux
environment).

- **`Dockerfile`** — one shared image for all four apps: Python +
  PyInstaller + the system libraries PyQt6's bundled Qt needs at
  runtime. Pinned to Ubuntu 22.04 for a deliberately conservative
  glibc floor (glibc is forward-compatible only — a binary built on a
  newer base won't run on an older user's system).
- **`build.sh`** — bind-mounts a given app repo into the image and
  runs `pip install -r requirements.txt` + `pyinstaller <spec>` inside
  it. No app source is ever baked into the image, so editing code
  never requires a rebuild — only re-running the script.

**Requires Docker Desktop installed and running.** Not yet installed
on every machine this project gets worked from — check before
assuming it's available.

Usage:
```bash
./linux-build/build.sh /c/Dev/videoredactor videoredactor.spec
./linux-build/build.sh /c/Dev/mp3redactor mp3redactor.spec --test   # also runs pytest first
```

Output lands in the app repo's own `dist/`, same layout as a normal
Windows PyInstaller build — just a Linux ELF binary instead of a
`.exe`. Each `.spec`'s `icon="assets/icon.ico"` is simply ignored on
Linux (icon embedding is a Windows/Mac-only PyInstaller concept), not
an error — fine for a first "does it build and run" pass; a real
Linux release would want its own icon/`.desktop`-file packaging (e.g.
via an AppImage) on top of this.

## License

No license file yet — this is internal tooling, not a distributed
product. Treat as all-rights-reserved until that's revisited.
