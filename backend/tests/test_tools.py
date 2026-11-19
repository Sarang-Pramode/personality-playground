"""Tests for allowlisted mock tools."""

import pytest

from app.tools.registry import ALLOWED_TOOLS, execute_tool, list_tool_names


def test_allowlist_complete():
    assert list_tool_names() == sorted(ALLOWED_TOOLS)
    assert len(ALLOWED_TOOLS) == 5


def test_customer_a_balance():
    result = execute_tool("get_rewards_balance", {"customer_id": "customer_A"})
    assert result["ok"] is True
    assert result["data"]["available"] == 42350


def test_customer_b_balance():
    result = execute_tool("get_rewards_balance", {"customer_id": "customer_B"})
    assert result["data"]["available"] == 12480


def test_unknown_tool_rejected():
    with pytest.raises(PermissionError):
        execute_tool("delete_account", {"customer_id": "customer_A"})


def test_unknown_customer():
    with pytest.raises(KeyError):
        execute_tool("get_customer_profile", {"customer_id": "customer_Z"})


def test_redemption_options_readonly():
    result = execute_tool("get_redemption_options", {"customer_id": "customer_A"})
    assert result["ok"]
    assert len(result["data"]) >= 3
    assert all("notes" in o for o in result["data"])


def test_transactions_limit():
    result = execute_tool(
        "get_rewards_transactions", {"customer_id": "customer_A", "limit": 2}
    )
    assert len(result["data"]) == 2
