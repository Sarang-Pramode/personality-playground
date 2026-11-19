"""Environment configuration — secrets stay server-side."""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    openai_api_key: str = ""
    google_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    google_model: str = "gemini-2.0-flash"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    # Prefer explicit origins when using cookie auth (cannot use * with credentials).
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    prompt_version: str = "personality-compiler-v1"

    # Auth / allowlist — set AUTH_ENABLED=true (or AUTH_REQUIRED=true) to gate APIs + UI.
    # Default false: open playground; auth code remains for later re-enable.
    auth_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AUTH_ENABLED", "AUTH_REQUIRED"),
    )
    database_url: str = "sqlite+pysqlite:///:memory:"
    session_secret: str = "dev-only-change-me-session-secret-32chars"
    data_encryption_key: str = ""  # Fernet key (url-safe base64); optional
    admin_email: str = "sarangpramode1997@gmail.com"
    # One-time admin password bootstrap (empty = disabled). Remove after use.
    bootstrap_token: str = ""
    app_base_url: str = "http://localhost:5173"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    session_cookie_name: str = "pp_session"
    session_ttl_hours: int = 168  # 7 days

    # Google OAuth (Sign-In)
    google_client_id: str = ""
    google_client_secret: str = ""

    # Admin notification email
    resend_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@personality-playground.local"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def openai_available(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def google_available(self) -> bool:
        return bool(self.google_api_key.strip())

    @property
    def any_llm_available(self) -> bool:
        return self.openai_available or self.google_available

    @property
    def google_oauth_configured(self) -> bool:
        return bool(self.google_client_id.strip() and self.google_client_secret.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
