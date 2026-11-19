"""Allowlisted read-only mock tools over synthetic fixtures."""

from __future__ import annotations

from typing import Any

from app.fixtures.data import FIXTURES

ALLOWED_TOOLS = frozenset(
    {
        "get_customer_profile",
        "get_customer_cards",
        "get_rewards_balance",
        "get_rewards_transactions",
        "get_redemption_options",
    }
)

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_profile",
            "description": "Return the synthetic customer profile for the active fixture.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Fixture customer id (customer_A or customer_B).",
                    }
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_cards",
            "description": "List cards linked to the synthetic customer.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rewards_balance",
            "description": "Return available and pending rewards balance.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rewards_transactions",
            "description": "Return recent rewards earn/burn transactions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_redemption_options",
            "description": "Return eligible redemption options and caveats.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
            },
        },
    },
]


def list_tool_names() -> list[str]:
    return sorted(ALLOWED_TOOLS)


def _fixture(customer_id: str) -> dict:
    if customer_id not in FIXTURES:
        raise KeyError(f"Unknown customer_id: {customer_id}")
    return FIXTURES[customer_id]


def execute_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute an allowlisted read-only tool. Raises on unknown tools."""
    if name not in ALLOWED_TOOLS:
        raise PermissionError(f"Tool not allowlisted: {name}")

    args = arguments or {}
    customer_id = args.get("customer_id")
    if not customer_id:
        raise ValueError("customer_id is required")

    data = _fixture(customer_id)

    if name == "get_customer_profile":
        return {"ok": True, "data": data["profile"]}
    if name == "get_customer_cards":
        return {"ok": True, "data": data["cards"]}
    if name == "get_rewards_balance":
        return {"ok": True, "data": data["rewards_balance"]}
    if name == "get_rewards_transactions":
        limit = int(args.get("limit") or 10)
        return {"ok": True, "data": data["transactions"][:limit]}
    if name == "get_redemption_options":
        return {"ok": True, "data": data["redemption_options"]}

    raise PermissionError(f"Tool not allowlisted: {name}")
