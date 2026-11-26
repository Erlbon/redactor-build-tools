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

## `devenv/`: each repo tests in its own `.venv`

`devenv/venv_sync.py` gives a repo its own `.venv`, holding exactly the redactor_common its pin names
(`requirements.txt`, or `pyproject.toml` when there is none), and prints that venv's python. Every
repo's `.githooks/pre-push` calls it first and runs pytest with the python it prints:

    PY="$(python ../redactor-build-tools/devenv/venv_sync.py .)" && "$PY" -m pytest

- **Why:** on 2026-11-04 all repos tested against one shared install of redactor_common while they were
  pinned to different tags; installing one repo's pin broke three other repos' pushes in one evening.
- **First run** makes `.venv` (with `--system-site-packages`, so PyQt6 and the other big packages come
  from the shared Python) and installs the requirements: about 30 s. redactor_common itself always goes
  *into* the venv; a shared copy seen through the system packages does not count.
- **Later runs** only check (about 0.3 s), and reinstall when `requirements.txt` changed or the venv's
  redactor_common is not the pinned version.
- **Rule:** never `pip install` a repo's requirements into the shared Python. Use the repo's venv:
  `.venv\Scripts\python -m pytest`, `.venv\Scripts\python bump_version.py`.
- The hooks find this repo next to the main checkout (so a push from a git worktree works too), or
  where `REDACTOR_BUILD_TOOLS` points. Clone it next to the app repos.
- **Builds use a second venv, `.venv-build`** (`venv_sync.py --build .`, called by each app's `build_exe.bat`):
  made *without* `--system-site-packages`, so it sees neither the shared Python's packages nor the user's own
  site-packages, only the requirements and PyInstaller. Through the test `.venv`, PyInstaller also bundled
  optional packages that happened to be installed on the PC (mp3redactor's exe, 2026-11-26: Pillow, lxml and
  cryptography, 75 MB became 95 MB). Releases are built on the PC since the update framework, so the build
  venv must be as clean as GitHub's runners were. It downloads everything once, then only checks.
- Tests: `python -m pytest devenv` (three of them make a real venv in a temp folder).

## License

No license file yet — this is internal tooling, not a distributed
product. Treat as all-rights-reserved until that's revisited.
