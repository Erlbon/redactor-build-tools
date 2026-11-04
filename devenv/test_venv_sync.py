"""Tests for venv_sync.py. The last two make a real venv in tmp_path (a few seconds); none needs the network."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import venv_sync  # noqa: E402

PINNED = "PyQt6>=6.6\nredactor_common @ git+https://github.com/Erlbon/redactor_common.git@2026-11-04-02\n"


def test_reads_the_pin_from_requirements_and_pyproject_lines():
    assert venv_sync.pinned_tag(PINNED) == "2026-11-04-02"
    line = '    "redactor_common @ git+https://github.com/Erlbon/redactor_common.git@2026-10-25-01",   # pin a tag'
    assert venv_sync.pinned_tag(line) == "2026-10-25-01"
    assert venv_sync.pinned_tag("PyQt6>=6.6\n") is None


def test_a_tag_becomes_the_version_pip_reports():
    assert venv_sync.version_of_tag("2026-11-04-02") == "2026.11.4.2"
    assert venv_sync.version_of_tag("2026-10-25-01") == "2026.10.25.1"


def test_requirements_txt_wins_over_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    assert venv_sync.requirement_file(tmp_path).name == "pyproject.toml"
    (tmp_path / "requirements.txt").write_text("", encoding="utf-8")
    assert venv_sync.requirement_file(tmp_path).name == "requirements.txt"


def test_the_fingerprint_follows_the_requirement_file(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("a\n", encoding="utf-8")
    first = venv_sync.fingerprint(req)
    req.write_text("b\n", encoding="utf-8")
    assert venv_sync.fingerprint(req) != first


def test_makes_a_venv_once_and_then_only_checks(tmp_path, monkeypatch):
    (tmp_path / "requirements.txt").write_text("# nothing pinned\n", encoding="utf-8")
    py = venv_sync.sync(tmp_path)
    assert py.exists() and (tmp_path / ".venv").is_dir()
    stamp = json.loads((tmp_path / ".venv" / venv_sync.STAMP).read_text(encoding="utf-8"))
    assert stamp["redactor_common"] is None
    calls = []
    monkeypatch.setattr(venv_sync, "run", lambda cmd: calls.append(cmd))
    assert venv_sync.sync(tmp_path) == py
    assert calls == []                                      # nothing changed: no venv made, nothing installed


def test_a_shared_copy_seen_through_the_system_packages_does_not_count(tmp_path):
    (tmp_path / "requirements.txt").write_text("# nothing pinned\n", encoding="utf-8")
    py = venv_sync.sync(tmp_path)
    fake = tmp_path / "shared" / "redactor_common-2026.11.4.2.dist-info"     # a copy outside the venv
    fake.mkdir(parents=True)
    (fake / "METADATA").write_text("Metadata-Version: 2.1\nName: redactor_common\nVersion: 2026.11.4.2\n", encoding="utf-8")
    probe = venv_sync.PROBE.replace("import importlib.metadata as m, json",
                                    "import importlib.metadata as m, json, sys; sys.path.insert(0, %r)" % str(fake.parent))
    out = subprocess.run([str(py), "-c", probe], capture_output=True, text=True, check=True)
    assert json.loads(out.stdout)[0] == "2026.11.4.2"      # the venv's python can see the shared copy...
    real = venv_sync.PROBE
    try:
        venv_sync.PROBE = probe
        assert venv_sync.own_redactor_common(py, tmp_path / ".venv") is None   # ...but it is not the venv's own
    finally:
        venv_sync.PROBE = real


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
