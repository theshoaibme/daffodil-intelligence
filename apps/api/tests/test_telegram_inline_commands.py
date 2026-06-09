"""Inline slash command parsing for Telegram."""

from app.integrations.telegram.commands import parse_inline_command


def test_parse_inline_command_with_args():
    assert parse_inline_command("/copycat record my_flow") == ("copycat", ["record", "my_flow"])


def test_parse_inline_command_bot_suffix():
    assert parse_inline_command("/copycat@daffodil_intelligence_bot record x") == (
        "copycat",
        ["record", "x"],
    )


def test_parse_inline_command_not_command():
    assert parse_inline_command("hello") is None
