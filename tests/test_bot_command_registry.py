import pytest


def test_bot_commands_registered(app):
    from erp.bots.dispatcher import COMMANDS

    expected = {
        "help",
        "whoami",
        "approve_action",
        "reject_action",
        "inventory_query",
        "analytics_query",
    }
    assert expected.issubset(COMMANDS.keys())


@pytest.mark.parametrize("role_name", ["admin", "employee"])
def test_whoami_reports_identity(app, make_user_with_role, role_name):
    from erp.bots.handlers import whoami

    user = make_user_with_role(role_name)
    with app.app_context():
        response = whoami({"user": user})
    assert "User:" in response["text"]
    assert role_name in response["text"]


def test_help_menu_lists_core_commands(app):
    from erp.bots.handlers import help_menu

    response = help_menu({})
    assert "Commands" in response["text"]
    assert "/help" in response["text"]
    assert "/whoami" in response["text"]
