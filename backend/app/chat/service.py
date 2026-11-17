"""In-memory chat sessions + orchestration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.config import Settings, get_settings
from app.llm.adapters import LLMUnavailableError, complete_chat
from app.personality.compiler import TraitProfile, compile_personality


@dataclass
class Session:
    session_id: str
    customer_id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ChatService:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def get_or_create(
        self, session_id: str | None, customer_id: str, *, reset: bool = False
    ) -> Session:
        if reset or not session_id or session_id not in self._sessions:
            sid = session_id or str(uuid.uuid4())
            session = Session(session_id=sid, customer_id=customer_id)
            self._sessions[sid] = session
            return session
        session = self._sessions[session_id]
        if session.customer_id != customer_id:
            session = Session(session_id=session_id, customer_id=customer_id)
            self._sessions[session_id] = session
        return session

    async def chat(
        self,
        *,
        message: str,
        customer_id: str,
        personality: dict[str, int] | None,
        preset: str | None,
        provider: str,
        model_id: str | None,
        session_id: str | None,
        scenario_id: str | None,
        reset_session: bool = False,
        settings: Settings | None = None,
    ) -> dict[str, Any]:
        settings = settings or get_settings()
        compiled = compile_personality(personality, preset=preset)
        session = self.get_or_create(
            session_id, customer_id, reset=reset_session
        )
        session.messages.append({"role": "user", "content": message})

        run_id = str(uuid.uuid4())
        try:
            result = await complete_chat(
                provider=provider,
                model_id=model_id,
                system_prompt=compiled["system_prompt"],
                messages=list(session.messages),
                customer_id=customer_id,
                settings=settings,
            )
            error = None
        except LLMUnavailableError as exc:
            result = {
                "reply": str(exc),
                "tool_traces": [],
                "mode": "error",
                "provider": provider,
                "model_id": model_id,
                "label": f"{provider} unavailable",
            }
            error = str(exc)

        assistant_text = result["reply"]
        if result.get("mode") != "error":
            session.messages.append({"role": "assistant", "content": assistant_text})

        return {
            "reply": assistant_text,
            "run_id": run_id,
            "session_id": session.session_id,
            "error": error,
            "metadata": {
                "profile": compiled["profile"],
                "preset": compiled.get("preset"),
                "prompt_version": settings.prompt_version,
                "policy_version": compiled["policy_version"],
                "fixture_id": customer_id,
                "scenario_id": scenario_id,
                "model_id": result.get("model_id"),
                "provider": result.get("provider"),
                "mode": result.get("mode"),
                "model_label": result.get("label"),
                "tool_traces": result.get("tool_traces", []),
                "system_prompt": compiled["system_prompt"],
                "behavior_summary": compiled["behavior_summary"],
                "run_id": run_id,
            },
        }


_service = ChatService()


def get_chat_service() -> ChatService:
    return _service
