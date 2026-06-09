"""VERSION file must match packaged metadata (CI gate)."""

from pathlib import Path

import daffodil_kit

ROOT = Path(__file__).resolve().parents[1]


def test_version_file_exists():
    vf = ROOT / "VERSION"
    assert vf.exists()
    v = vf.read_text().strip()
    assert len(v.split(".")) == 3


def test_version_matches_init():
    file_v = (ROOT / "VERSION").read_text().strip()
    assert daffodil_kit.__version__ == file_v


def test_pyproject_version_matches():
    import re

    text = (ROOT / "pyproject.toml").read_text()
    m = re.search(r'^version = "(.+)"$', text, re.M)
    assert m
    assert m.group(1) == (ROOT / "VERSION").read_text().strip()


def test_install_scripts_exist():
    repo_root = ROOT.parents[1]
    assert (repo_root / "install").exists()
    assert (repo_root / "install.ps1").exists()
    assert (ROOT / "install").exists()
    assert (ROOT / "install.py").exists()
    assert (ROOT / "install.sh").exists()
    assert (ROOT / "install.ps1").exists()
    assert (ROOT / "scripts" / "bootstrap-python.sh").exists()
