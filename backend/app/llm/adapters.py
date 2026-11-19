"""OpenAI + Google adapters with explicit scripted demo fallback."""

from __future__ import annotations

import json
from typing import Any

from app.config import Settings, get_settings
from app.llm.allowlist import (
    OPENAI_ALLOWED_MODELS,
    is_openai_model_allowed,
    resolve_openai_model,
)
from app.tools.registry import TOOL_DEFINITIONS, execute_tool


class LLMUnavailableError(RuntimeError):
    """Raised when a live provider is requested but not configured."""


class ModelNotAllowedError(ValueError):
    """Raised when a client requests a non-allowlisted OpenAI model."""


def list_models(settings: Settings | None = None) -> list[dict[str, Any]]:
    """Return switcher options — OpenAI entries are allowlisted small models only."""
    settings = settings or get_settings()
    models: list[dict[str, Any]] = []
    for mid in OPENAI_ALLOWED_MODELS:
        available = settings.openai_available
        suffix = "" if available else " (key missing)"
        models.append(
            {
                "provider": "openai",
                "model_id": mid,
                "label": f"OpenAI · {mid}{suffix}",
                "available": available,
            }
        )
    if settings.google_available:
        models.append(
            {
                "provider": "google",
                "model_id": settings.google_model,
                "label": f"Google · {settings.google_model}",
                "available": True,
            }
        )
    else:
        models.append(
            {
                "provider": "google",
                "model_id": settings.google_model,
                "label": f"Google · {settings.google_model} (key missing)",
                "available": False,
            }
        )
    models.append(
        {
            "provider": "demo",
            "model_id": "scripted-demo",
            "label": "Scripted demo mode (no LLM)",
            "available": True,
        }
    )
    return models


async def complete_chat(
    *,
    provider: str,
    model_id: str | None,
    system_prompt: str,
    messages: list[dict[str, str]],
    customer_id: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """
    Run a non-streaming chat turn with optional tool calls.

    Returns reply, tool_traces, mode ('live'|'scripted_demo'), model metadata.
    """
    settings = settings or get_settings()
    provider = (provider or "").lower().strip()

    if provider == "demo" or provider == "scripted":
        return await _scripted_demo(messages=messages, customer_id=customer_id)

    if provider == "openai":
        if not settings.openai_available:
            raise LLMUnavailableError(
                "OpenAI is not configured. Set OPENAI_API_KEY or switch to Google / Scripted demo mode."
            )
        requested = model_id or settings.openai_model
        if not is_openai_model_allowed(requested):
            raise ModelNotAllowedError(
                f"OpenAI model '{requested}' is not allowlisted. "
                f"Allowed: {', '.join(OPENAI_ALLOWED_MODELS)}"
            )
        resolved = resolve_openai_model(requested, settings.openai_model)
        return await _openai_chat(
            model_id=resolved,
            system_prompt=system_prompt,
            messages=messages,
            customer_id=customer_id,
            api_key=settings.openai_api_key,
        )

    if provider == "google":
        if not settings.google_available:
            raise LLMUnavailableError(
                "Google is not configured. Set GOOGLE_API_KEY or switch to OpenAI / Scripted demo mode."
            )
        return await _google_chat(
            model_id=model_id or settings.google_model,
            system_prompt=system_prompt,
            messages=messages,
            customer_id=customer_id,
            api_key=settings.google_api_key,
        )

    raise LLMUnavailableError(
        f"Unknown provider '{provider}'. Use openai, google, or demo."
    )


async def _scripted_demo(
    *, messages: list[dict[str, str]], customer_id: str
) -> dict[str, Any]:
    """Deterministic fixture-backed reply — explicitly labeled, never silent fake live."""
    user_text = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
    ).lower()

    traces: list[dict[str, Any]] = []

    def call(name: str, **kwargs: Any) -> Any:
        result = execute_tool(name, {"customer_id": customer_id, **kwargs})
        traces.append(
            {
                "tool": name,
                "arguments": {"customer_id": customer_id, **kwargs},
                "result": result,
            }
        )
        return result["data"]

    balance = call("get_rewards_balance")
    profile = call("get_customer_profile")

    if any(
        k in user_text
        for k in ("unlimited companion", "another agent promised", "lifetime")
    ):
        reply = (
            f"[Scripted demo mode — no live LLM] Hi {profile['name']}. "
            "I can't confirm unlimited companion tickets or other benefits that "
            "aren't in your fixture data. From tools, your available balance is "
            f"{balance['available']} {balance['currency']} "
            f"({balance.get('pending', 0)} pending). "
            "I can only describe verified redemption options if you ask."
        )
    elif any(
        k in user_text
        for k in ("ignore your banking", "waive", "wire me a cash", "no eligibility")
    ):
        reply = (
            f"[Scripted demo mode — no live LLM] Hi {profile['name']}. "
            "I can't ignore banking policy or skip eligibility checks. "
            f"Your available balance is {balance['available']} {balance['currency']}. "
            "I can list verified redemption options that exist in the fixtures."
        )
    elif any(k in user_text for k in ("redeem", "redemption", "option", "best way", "tradeoff", "eligibility", "structured breakdown", "every verified")):
        options = call("get_redemption_options")
        lines = [
            f"[Scripted demo mode — no live LLM] Hi {profile['name']}.",
            f"You have {balance['available']} {balance['currency']} available "
            f"({balance.get('pending', 0)} pending).",
            "Redemption options from fixtures:",
        ]
        for opt in options:
            lines.append(
                f"- {opt['name']}: min {opt['min_points']} pts "
                f"(~${opt['value_per_point_usd']}/pt). Note: {opt['notes']}"
            )
        reply = "\n".join(lines)
    elif any(k in user_text for k in ("transaction", "activity", "recent", "history")):
        txns = call("get_rewards_transactions", limit=5)
        lines = [
            f"[Scripted demo mode — no live LLM] Recent activity for {profile['name']}:",
        ]
        for t in txns:
            lines.append(f"- {t['date']}: {t['description']} (+{t['points']})")
        lines.append(
            f"Available balance: {balance['available']} {balance['currency']}."
        )
        reply = "\n".join(lines)
    elif any(k in user_text for k in ("card", "earn", "rate")):
        cards = call("get_customer_cards")
        lines = [f"[Scripted demo mode — no live LLM] Cards for {profile['name']}:"]
        for c in cards:
            lines.append(
                f"- {c['name']} (····{c['last_four']}): {c['earn_rate_summary']} "
                f"(annual fee ${c['annual_fee']})"
            )
        reply = "\n".join(lines)
    else:
        # Default path covers balance, frustration, warmth, steadiness, ambiguity.
        pending = balance.get("pending", 0)
        reply = (
            f"[Scripted demo mode — no live LLM] Hi {profile['name']}. "
            f"Your available rewards balance is {balance['available']} "
            f"{balance['currency']} as of {balance['as_of']} "
            f"({pending} pending — pending is not yet spendable). "
            "Ask about redemptions, cards, or recent activity for more detail."
        )

    return {
        "reply": reply,
        "tool_traces": traces,
        "mode": "scripted_demo",
        "provider": "demo",
        "model_id": "scripted-demo",
        "label": "Scripted demo mode (no live LLM)",
    }


async def _openai_chat(
    *,
    model_id: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    customer_id: str,
    api_key: str,
) -> dict[str, Any]:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    traces: list[dict[str, Any]] = []
    openai_messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        *[{"role": m["role"], "content": m["content"]} for m in messages],
    ]

    for _ in range(4):
        response = await client.chat.completions.create(
            model=model_id,
            messages=openai_messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )
        choice = response.choices[0]
        msg = choice.message

        if msg.tool_calls:
            openai_messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                args.setdefault("customer_id", customer_id)
                try:
                    result = execute_tool(tc.function.name, args)
                except Exception as exc:  # noqa: BLE001
                    result = {"ok": False, "error": str(exc)}
                traces.append(
                    {
                        "tool": tc.function.name,
                        "arguments": args,
                        "result": result,
                    }
                )
                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
            continue

        return {
            "reply": (msg.content or "").strip(),
            "tool_traces": traces,
            "mode": "live",
            "provider": "openai",
            "model_id": model_id,
            "label": f"OpenAI · {model_id}",
        }

    return {
        "reply": "I hit the tool-call limit for this turn. Please try a simpler question.",
        "tool_traces": traces,
        "mode": "live",
        "provider": "openai",
        "model_id": model_id,
        "label": f"OpenAI · {model_id}",
    }


async def _google_chat(
    *,
    model_id: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    customer_id: str,
    api_key: str,
) -> dict[str, Any]:
    """Google GenAI with function declarations (read-only tools)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    traces: list[dict[str, Any]] = []

    def to_gemini_fn(defn: dict) -> types.FunctionDeclaration:
        fn = defn["function"]
        return types.FunctionDeclaration(
            name=fn["name"],
            description=fn.get("description"),
            parameters=fn.get("parameters"),
        )

    tools = [
        types.Tool(function_declarations=[to_gemini_fn(d) for d in TOOL_DEFINITIONS])
    ]

    contents: list[types.Content] = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=m["content"])])
        )

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=tools,
    )

    for _ in range(4):
        response = await client.aio.models.generate_content(
            model=model_id,
            contents=contents,
            config=config,
        )

        candidate = response.candidates[0] if response.candidates else None
        if not candidate or not candidate.content:
            break

        parts = candidate.content.parts or []
        fn_calls = [p for p in parts if getattr(p, "function_call", None)]

        if fn_calls:
            contents.append(candidate.content)
            response_parts: list[types.Part] = []
            for part in fn_calls:
                fc = part.function_call
                args = dict(fc.args or {})
                args.setdefault("customer_id", customer_id)
                try:
                    result = execute_tool(fc.name, args)
                except Exception as exc:  # noqa: BLE001
                    result = {"ok": False, "error": str(exc)}
                traces.append(
                    {"tool": fc.name, "arguments": args, "result": result}
                )
                response_parts.append(
                    types.Part.from_function_response(name=fc.name, response=result)
                )
            contents.append(types.Content(role="user", parts=response_parts))
            continue

        text = "".join(
            getattr(p, "text", "") or "" for p in parts if getattr(p, "text", None)
        ).strip()
        return {
            "reply": text,
            "tool_traces": traces,
            "mode": "live",
            "provider": "google",
            "model_id": model_id,
            "label": f"Google · {model_id}",
        }

    # Fallback: if no text, still return traces
    return {
        "reply": (getattr(response, "text", None) or "").strip()
        or "No response generated.",
        "tool_traces": traces,
        "mode": "live",
        "provider": "google",
        "model_id": model_id,
        "label": f"Google · {model_id}",
    }
