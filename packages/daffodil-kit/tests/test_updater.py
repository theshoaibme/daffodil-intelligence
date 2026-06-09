"""Updater version logic (no network)."""

from daffodil_kit.updater import is_newer, parse_version


def test_parse_version():
    assert parse_version("0.1.0") == (0, 1, 0)
    assert parse_version("1.2.3") == (1, 2, 3)


def test_is_newer():
    assert is_newer("0.2.0", "0.1.0")
    assert is_newer("0.1.1", "0.1.0")
    assert not is_newer("0.1.0", "0.1.0")
    assert not is_newer("0.1.0", "0.2.0")
