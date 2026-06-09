"""Telegram bot command menu helpers."""

from app.integrations.telegram.commands import (
    AUTHENTICATED_COMMAND_LABELS,
    GUEST_COMMAND_LABELS,
    default_authenticated_message,
    default_guest_message,
    help_text,
    parse_suggestion_text,
    step_empty_prompt,
)


def test_guest_command_labels():
    assert "register" in GUEST_COMMAND_LABELS
    assert "login" in GUEST_COMMAND_LABELS
    assert "record" not in GUEST_COMMAND_LABELS


def test_authenticated_command_labels():
    assert "record" in AUTHENTICATED_COMMAND_LABELS
    assert "recordings" in AUTHENTICATED_COMMAND_LABELS
    assert "replay" in AUTHENTICATED_COMMAND_LABELS
    assert "register" not in AUTHENTICATED_COMMAND_LABELS


def test_help_text_includes_all_authenticated_commands():
    text = help_text(authenticated=True)
    for name in AUTHENTICATED_COMMAND_LABELS:
        assert f"/{name}" in text


def test_help_text_includes_guest_commands():
    text = help_text(authenticated=False)
    for name in GUEST_COMMAND_LABELS:
        assert f"/{name}" in text


def test_parse_suggestion_text():
    assert parse_suggestion_text("Register") == "register"
    assert parse_suggestion_text("LOGIN") == "login"
    assert parse_suggestion_text("Help") == "help"
    assert parse_suggestion_text("hello") is None


def test_default_messages_are_non_empty():
    assert "Daffodil" in default_guest_message()
    assert "help" in default_authenticated_message().lower()


def test_step_empty_prompts():
    assert "email" in step_empty_prompt("register_email").lower()
    assert "role" in step_empty_prompt("register_role").lower()
    assert step_empty_prompt("auth_menu") == default_guest_message()
