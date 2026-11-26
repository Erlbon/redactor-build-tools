"""venv_sync.py -- give a repo its own .venv, holding exactly the redactor_common its pin names, and print that venv's python.

Why (2026-11-04): every repo's tests and pre-push hook used one shared install of redactor_common, while the repos were pinned to
different tags. Installing the pin of one repo broke the others: three pushes failed in one evening with "No module named
redactor_common.core.lookups". Now each repo tests in its own .venv, and the hook calls this script first, so a wrong version
is repaired before the tests run and nobody has to remember to reinstall.

What it does, in <repo>:
- makes .venv if it is missing (with --system-site-packages: PyQt6 and the other big packages come from the shared Python,
  so a venv is small and quick to make; redactor_common itself is always installed INTO the venv, never borrowed);
- reads the pin `redactor_common @ git+https://github.com/Erlbon/redactor_common.git@YYYY-MM-DD-NN` from requirements.txt
  (or pyproject.toml when there is no requirements.txt);
- installs the requirements again only when the requirement file changed or the venv's own redactor_common is not the pinned
  version; otherwise it costs one quick version check;
- prints the venv's python (forward slashes) on stdout. Messages go to stderr.

Usage (from a hook):  PY="$(python <tools>/devenv/venv_sync.py <repo>)" && "$PY" -m pytest
Standard library only: it runs before anything is installed.

--build (2026-11-26): the same for <repo>/.venv-build, the venv the exe and the installer are built in. It does NOT see the
shared Python's packages (nor the user's own site-packages), so PyInstaller bundles only what the requirements install.
Through --system-site-packages it also bundled whatever optional package happened to be installed on the PC: mp3redactor's
exe grew from 75 to 95 MB with Pillow, lxml and cryptography, which music_tag, bs4 and requests import when they find them.
Since releases are built on the PC (redactor_common's release tool), not on GitHub's clean runners, the build venv must be
as clean as theirs. It is made once (it downloads PyQt6 and the rest) and then only checked, like .venv.

Usage (from build_exe.bat):  python <tools>/devenv/venv_sync.py --build <repo>
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PIN = re.compile(r"redactor_common\s*@\s*git\+https://github\.com/Erlbon/redactor_common\.git@(\d{4}-\d{2}-\d{2}-\d{2})")
STAMP = "redactor-venv.json"
TEST_VENV = ".venv"           # tests: the shared Python's packages seen through --system-site-packages
BUILD_VENV = ".venv-build"    # builds: nothing but the requirements (and PyInstaller)
PROBE = ("import importlib.metadata as m, json\n"
         "try:\n"
         "    d = m.distribution('redactor_common')\n"
         "    print(json.dumps([d.version, str(d.locate_file(''))]))\n"
         "except m.PackageNotFoundError:\n"
         "    print(json.dumps(None))\n")


def say(text):
    print("venv_sync: " + text, file=sys.stderr)


def pinned_tag(text):
    """The redactor_common tag a requirement file pins, such as '2026-11-04-02', or None."""
    found = PIN.search(text)
    return found.group(1) if found else None


def version_of_tag(tag):
    """The package version a tag installs as: '2026-11-04-02' -> '2026.11.4.2'."""
    return ".".join(str(int(part)) for part in tag.split("-"))


def requirement_file(repo):
    """requirements.txt when the repo has one, else pyproject.toml, else None."""
    for name in ("requirements.txt", "pyproject.toml"):
        path = repo / name
        if path.is_file():
            return path
    return None


def venv_python(venv):
    windows = venv / "Scripts" / "python.exe"
    return windows if windows.exists() or sys.platform == "win32" else venv / "bin" / "python"


def fingerprint(req):
    data = req.read_bytes() if req else b""
    return hashlib.sha256(data + sys.version.encode()).hexdigest()


def own_redactor_common(py, venv):
    """The redactor_common version installed inside this venv itself, or None (missing, or only the shared one is seen)."""
    out = subprocess.run([str(py), "-c", PROBE], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    found = json.loads(out.stdout.strip() or "null")
    if not found:
        return None
    version, where = found
    try:
        Path(where).resolve().relative_to(venv.resolve())
    except ValueError:
        return None                                          # seen through --system-site-packages: not the venv's own
    return version


def run(cmd):
    done = subprocess.run([str(c) for c in cmd])
    if done.returncode != 0:
        raise SystemExit("venv_sync: failed (exit %d): %s" % (done.returncode, " ".join(str(c) for c in cmd)))


def sync(repo, base_python=sys.executable, build=False):
    """Make <repo>/.venv (build: <repo>/.venv-build, without the shared packages) right and return its python."""
    repo = Path(repo).resolve()
    venv = repo / (BUILD_VENV if build else TEST_VENV)
    py = venv_python(venv)
    if not py.exists():
        say("making %s%s" % (venv, " (clean: the first time it downloads every requirement)" if build else ""))
        run([base_python, "-m", "venv", venv] if build else [base_python, "-m", "venv", "--system-site-packages", venv])
        py = venv_python(venv)
    req = requirement_file(repo)
    tag = pinned_tag(req.read_text(encoding="utf-8")) if req else None
    want = version_of_tag(tag) if tag else None
    stamp_path = venv / STAMP
    try:
        stamp = json.loads(stamp_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        stamp = {}
    current = fingerprint(req)
    if stamp.get("fingerprint") == current and (want is None or own_redactor_common(py, venv) == want):
        return py
    if req is not None and req.name == "requirements.txt":
        say("installing %s into %s" % (req.name, venv.name))
        run([py, "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", req])
    elif req is not None:
        say("installing the project (editable) into %s" % venv.name)
        run([py, "-m", "pip", "install", "-q", "--disable-pip-version-check", "-e", repo])
    if build:
        run([py, "-m", "pip", "install", "-q", "--disable-pip-version-check", "pyinstaller>=6.6"])
    if want is not None and own_redactor_common(py, venv) != want:
        say("installing redactor_common %s into %s" % (tag, venv.name))
        run([py, "-m", "pip", "install", "-q", "--disable-pip-version-check", "--force-reinstall", "--no-deps",
             "redactor_common @ git+https://github.com/Erlbon/redactor_common.git@" + tag])
        have = own_redactor_common(py, venv)
        if have != want:
            raise SystemExit("venv_sync: %s has redactor_common %s, the pin wants %s" % (venv.name, have, want))
    stamp_path.write_text(json.dumps({"fingerprint": current, "redactor_common": want}), encoding="utf-8")
    return py


def main(argv):
    args = argv[1:]
    build = "--build" in args
    args = [a for a in args if a != "--build"]
    repo = Path(args[0]) if args else Path(".")
    print(Path(sync(repo, build=build)).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
