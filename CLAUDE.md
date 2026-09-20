# redactor-build-tools

Cross-machine, git-tracked build tooling for the Redactor family (cbzredactor, epubredactor, mp3redactor, videoredactor). Currently one piece: a Docker-based Linux build toolchain. Split out from the machine-local `_shared-tools` folder (release scripts, a hand-placed `upx.exe`) deliberately — this repo holds only small, portable, plain-text tooling with no reason to be copied by hand between machines.

## Commands
- Build a Linux binary of an app: `./linux-build/build.sh /c/Dev/<app> <app>.spec` (add `--test` to run `pytest` first)
- Requires Docker Desktop installed and running — not yet installed on every machine this is worked from; check before assuming it's available.

## Layout
`linux-build/Dockerfile` (one shared image: Python + PyInstaller + the system libraries PyQt6's bundled Qt needs at runtime, pinned to Ubuntu 22.04 for a conservative glibc floor), `linux-build/build.sh` (bind-mounts the given app repo into the image and runs `pip install` + `pyinstaller` inside it — no app source is baked into the image, so a rebuild is never needed after an app code change, only a re-run).

## Domain notes
- Output lands in the app repo's own `dist/`, same layout as a normal Windows PyInstaller build, just a Linux ELF binary.
- Each `.spec`'s `icon="assets/icon.ico"` is silently ignored on Linux (icon embedding is a Windows/Mac-only PyInstaller concept) — not an error, fine for a first "does it build and run" pass. A real Linux release would want its own icon/`.desktop` packaging (e.g. an AppImage) on top of this.
- This is the concrete first piece of the family's Linux/Mac porting goal — Linux was chosen to start with since it needs no code-signing tax and Docker/WSL2 on Windows already provide a real Linux environment.
- No license file yet — internal tooling, not a distributed product; treat as all-rights-reserved until that's revisited.

## Family conventions that apply here
- **Sync first** — other sessions may edit this repo too. Before editing, and again right before every `git push`: `git fetch origin -q; git status --porcelain -b`. Confirm you match origin and the tree is clean. Fast-forward if behind; resolve if diverged.
- **Cross-platform goal** — this repo exists to serve that goal directly; keep the Dockerfile/build script working as the apps' own Windows-only assumptions get cleaned up elsewhere in the family.
- Version-bump, progress-feedback, promote-to-redactor_common, and landing-page rules don't apply to this repo (no `APP_VERSION`, no per-book loops, no GUI, not featured on the landing page).

Full family conventions: `.claude/skills/redactor-conventions/SKILL.md` in [redactor_common](https://github.com/Erlbon/redactor_common).
