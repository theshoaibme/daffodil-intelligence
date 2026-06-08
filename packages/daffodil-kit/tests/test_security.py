"""Security: HMAC command signing, vault local-only, config isolation."""

import time

from daffodil_kit.security import (
    generate_device_secret,
    get_or_create_device_id,
    load_config,
    save_config,
    sign_command,
    verify_command,
)


def test_hmac_sign_and_verify():
    secret = generate_device_secret()
    payload = '{"method":"mouse.click","params":{"x":1,"y":2}}'
    ts = time.time()
    sig = sign_command(secret, payload, ts)
    assert verify_command(secret, payload, ts, sig)
    assert not verify_command(secret, payload, ts, "deadbeef")
    assert not verify_command(secret, payload, ts + 120, sig)


def test_hmac_rejects_expired_timestamp():
    secret = generate_device_secret()
    payload = "{}"
    old_ts = time.time() - 120
    sig = sign_command(secret, payload, old_ts)
    assert not verify_command(secret, payload, old_ts, sig, max_age=60)


def test_device_secret_length():
    assert len(generate_device_secret()) == 64


def test_device_id_stable(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    monkeypatch.setattr("daffodil_kit.security.CONFIG_FILE", cfg_file)
    monkeypatch.setattr("daffodil_kit.security.CONFIG_DIR", tmp_path)
    a = get_or_create_device_id()
    b = get_or_create_device_id()
    assert a == b
    assert len(a) == 32


def test_config_roundtrip(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    monkeypatch.setattr("daffodil_kit.security.CONFIG_FILE", cfg_file)
    monkeypatch.setattr("daffodil_kit.security.CONFIG_DIR", tmp_path)
    save_config({"api_url": "http://localhost:8000", "paired": False})
    loaded = load_config()
    assert loaded["api_url"] == "http://localhost:8000"


def test_vault_local_only(tmp_path, monkeypatch):
    from daffodil_kit import vault

    monkeypatch.setattr(vault, "VAULT_DIR", tmp_path / "vault")
    monkeypatch.setattr(vault, "VAULT_FILE", tmp_path / "vault" / "secrets.enc")
    monkeypatch.setattr(vault, "META_FILE", tmp_path / "vault" / "meta.json")

    r = vault.set_system_password("test-secret", label="sudo")
    assert r["local_only"] is True
    assert vault.get_system_password("sudo") == "test-secret"
    assert vault.vault_status()["configured"] is True
    vault.clear_vault()
    assert vault.vault_status()["configured"] is False
