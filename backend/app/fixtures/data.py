"""Synthetic banking fixtures — customer_A / customer_B and demo scenarios."""

from __future__ import annotations

FIXTURES: dict[str, dict] = {
    "customer_A": {
        "customer_id": "customer_A",
        "display_name": "Alex Rivera",
        "segment": "travel_rewards",
        "profile": {
            "customer_id": "customer_A",
            "name": "Alex Rivera",
            "tier": "Gold",
            "member_since": "2019-04-12",
            "preferred_categories": ["travel", "dining"],
            "home_airport": "JFK",
        },
        "cards": [
            {
                "card_id": "card_A1",
                "name": "Voyager Infinite",
                "network": "Visa",
                "last_four": "4242",
                "rewards_type": "points",
                "earn_rate_summary": "3x travel, 2x dining, 1x other",
                "annual_fee": 95,
                "status": "active",
            },
            {
                "card_id": "card_A2",
                "name": "City Everyday",
                "network": "Mastercard",
                "last_four": "8811",
                "rewards_type": "points",
                "earn_rate_summary": "1.5x all purchases",
                "annual_fee": 0,
                "status": "active",
            },
        ],
        "rewards_balance": {
            "customer_id": "customer_A",
            "currency": "points",
            "available": 42350,
            "pending": 1200,
            "as_of": "2026-11-17",
        },
        "transactions": [
            {
                "txn_id": "txn_A1",
                "date": "2026-11-10",
                "description": "Airline ticket — Delta",
                "points": 4500,
                "category": "travel",
                "card_id": "card_A1",
            },
            {
                "txn_id": "txn_A2",
                "date": "2026-11-05",
                "description": "Hotel — Marriott Downtown",
                "points": 2800,
                "category": "travel",
                "card_id": "card_A1",
            },
            {
                "txn_id": "txn_A3",
                "date": "2026-10-28",
                "description": "Restaurant — Nobu",
                "points": 640,
                "category": "dining",
                "card_id": "card_A1",
            },
        ],
        "redemption_options": [
            {
                "option_id": "red_A1",
                "name": "Transfer to airline partners",
                "min_points": 5000,
                "value_per_point_usd": 0.015,
                "notes": "1:1 to select airline partners; transfers irreversible",
                "eligible": True,
            },
            {
                "option_id": "red_A2",
                "name": "Travel portal booking",
                "min_points": 2500,
                "value_per_point_usd": 0.012,
                "notes": "Flights and hotels via portal; taxes may apply in cash",
                "eligible": True,
            },
            {
                "option_id": "red_A3",
                "name": "Statement credit",
                "min_points": 2500,
                "value_per_point_usd": 0.01,
                "notes": "Lower value than travel transfers",
                "eligible": True,
            },
        ],
    },
    "customer_B": {
        "customer_id": "customer_B",
        "display_name": "Jordan Lee",
        "segment": "cash_back",
        "profile": {
            "customer_id": "customer_B",
            "name": "Jordan Lee",
            "tier": "Silver",
            "member_since": "2021-09-01",
            "preferred_categories": ["groceries", "gas"],
            "home_airport": None,
        },
        "cards": [
            {
                "card_id": "card_B1",
                "name": "CashBack Everyday",
                "network": "Visa",
                "last_four": "1199",
                "rewards_type": "cash_back",
                "earn_rate_summary": "3% groceries, 2% gas, 1% other",
                "annual_fee": 0,
                "status": "active",
            }
        ],
        "rewards_balance": {
            "customer_id": "customer_B",
            "currency": "cash_back_points",
            "available": 12480,
            "pending": 320,
            "as_of": "2026-11-17",
            "approx_cash_value_usd": 124.80,
        },
        "transactions": [
            {
                "txn_id": "txn_B1",
                "date": "2026-11-12",
                "description": "Grocery — FreshMart",
                "points": 540,
                "category": "groceries",
                "card_id": "card_B1",
            },
            {
                "txn_id": "txn_B2",
                "date": "2026-11-08",
                "description": "Gas — QuickFuel",
                "points": 210,
                "category": "gas",
                "card_id": "card_B1",
            },
            {
                "txn_id": "txn_B3",
                "date": "2026-10-30",
                "description": "Online retail — ShopCo",
                "points": 85,
                "category": "other",
                "card_id": "card_B1",
            },
        ],
        "redemption_options": [
            {
                "option_id": "red_B1",
                "name": "Deposit to checking",
                "min_points": 2500,
                "value_per_point_usd": 0.01,
                "notes": "Posted within 1–2 business days",
                "eligible": True,
            },
            {
                "option_id": "red_B2",
                "name": "Statement credit",
                "min_points": 2500,
                "value_per_point_usd": 0.01,
                "notes": "Applies to current card balance",
                "eligible": True,
            },
            {
                "option_id": "red_B3",
                "name": "Gift cards",
                "min_points": 5000,
                "value_per_point_usd": 0.01,
                "notes": "Select retailers only",
                "eligible": True,
            },
        ],
    },
}

SCENARIOS: list[dict] = [
    {
        "scenario_id": "balance_check",
        "title": "Check rewards balance",
        "description": "Customer asks how many points/cash-back they currently have.",
        "suggested_prompt": "How many rewards do I have available right now?",
        "fixture_ids": ["customer_A", "customer_B"],
    },
    {
        "scenario_id": "redemption_options",
        "title": "Compare redemption options",
        "description": "Customer wants the best way to use their rewards.",
        "suggested_prompt": "What are my best options for redeeming rewards?",
        "fixture_ids": ["customer_A", "customer_B"],
    },
    {
        "scenario_id": "recent_activity",
        "title": "Explain recent earn activity",
        "description": "Customer asks why their balance changed recently.",
        "suggested_prompt": "Can you walk me through my recent rewards activity?",
        "fixture_ids": ["customer_A", "customer_B"],
    },
    {
        "scenario_id": "card_earn_rates",
        "title": "Card earn-rate summary",
        "description": "Customer wants to know how their cards earn.",
        "suggested_prompt": "How do my cards earn rewards?",
        "fixture_ids": ["customer_A", "customer_B"],
    },
]


def list_fixtures() -> dict:
    return {
        "customers": [
            {
                "customer_id": c["customer_id"],
                "display_name": c["display_name"],
                "segment": c["segment"],
                "available_balance": c["rewards_balance"]["available"],
                "currency": c["rewards_balance"]["currency"],
            }
            for c in FIXTURES.values()
        ],
        "scenarios": SCENARIOS,
    }
