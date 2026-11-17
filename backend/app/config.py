"""Environment configuration — secrets stay server-side."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    google_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    google_model: str = "gemini-2.0-flash"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    prompt_version: str = "personality-compiler-v1"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
