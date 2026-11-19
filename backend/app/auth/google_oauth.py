"""Google OAuth 2.0 authorization-code flow."""

from __future__ import annotations

from urllib.parse import urlencode

import httpx

from app.config import Settings, get_settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def google_redirect_uri(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    base = settings.app_base_url.rstrip("/")
    return f"{base}/api/auth/google/callback"


def build_google_auth_url(state: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": google_redirect_uri(settings),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "include_granted_scopes": "true",
        "state": state,
        "prompt": "select_account",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


async def exchange_google_code(code: str, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    async with httpx.AsyncClient(timeout=20.0) as client:
        token_resp = await client.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": google_redirect_uri(settings),
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()
        access = tokens.get("access_token")
        if not access:
            raise RuntimeError("Google token response missing access_token")
        info_resp = await client.get(
            USERINFO_URL, headers={"Authorization": f"Bearer {access}"}
        )
        info_resp.raise_for_status()
        return info_resp.json()
