"""CopyCat guard and version tests (no display required)."""

from daffodil_kit.copycat_guard import (
    ALLOWED_DURING_LOCK,
    BLOCKED_METHODS,
    check_method_allowed,
)
from daffodil_kit import __version__


def test_version_is_semver():
    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_blocked_methods_defined():
    assert "mouse.click" in BLOCKED_METHODS
    assert "keyboard.type" in BLOCKED_METHODS
    assert "record.status" in ALLOWED_DURING_LOCK


def test_check_allowed_when_unlocked():
    assert check_method_allowed("mouse.click") is None


def test_check_blocked_when_locked(monkeypatch):
    monkeypatch.setattr("daffodil_kit.copycat_guard.is_locked", lambda: True)
    err = check_method_allowed("mouse.click")
    assert err is not None
    assert err["error"] == "copycat_running"
    assert err["blocked"] is True


def test_status_allowed_when_locked(monkeypatch):
    monkeypatch.setattr("daffodil_kit.copycat_guard.is_locked", lambda: True)
    assert check_method_allowed("record.status") is None
