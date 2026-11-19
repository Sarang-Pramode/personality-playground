"""Database engine + lightweight migrations."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def _normalize_url(url: str) -> str:
    # Neon / Heroku style postgres:// → SQLAlchemy
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def get_engine(settings: Settings | None = None) -> Engine:
    global _engine, _SessionLocal
    settings = settings or get_settings()
    if _engine is None:
        url = _normalize_url(settings.database_url)
        kwargs: dict = {"pool_pre_ping": True}
        if url.startswith("sqlite"):
            # Keep a single shared in-memory connection for tests / local default.
            kwargs["connect_args"] = {"check_same_thread": False}
            if ":memory:" in url:
                kwargs["poolclass"] = StaticPool
        _engine = create_engine(url, **kwargs)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    get_engine(settings)
    assert _SessionLocal is not None
    return _SessionLocal


def reset_engine() -> None:
    """Test helper — drop cached engine."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def run_migrations(settings: Settings | None = None) -> None:
    engine = get_engine(settings)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
        )
        applied = {
            row[0]
            for row in conn.execute(text("SELECT id FROM schema_migrations")).fetchall()
        }
        files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for path in files:
            mid = path.name
            if mid in applied:
                continue
            sql = path.read_text(encoding="utf-8")
            # SQLite vs Postgres: IF NOT EXISTS is fine for both for our DDL
            for stmt in _split_sql(sql):
                conn.execute(text(stmt))
            conn.execute(
                text(
                    "INSERT INTO schema_migrations (id, applied_at) VALUES (:id, :ts)"
                ),
                {"id": mid, "ts": _utcnow()},
            )


def _split_sql(sql: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        buf.append(line)
        if line.rstrip().endswith(";"):
            stmt = "\n".join(buf).strip().rstrip(";").strip()
            if stmt:
                parts.append(stmt)
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _utcnow() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
