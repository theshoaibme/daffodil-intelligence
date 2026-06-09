"""Synchronous PostgreSQL sessions for bot handlers and sync stores."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .database import is_mock_database

_settings = get_settings()
_sync_engine = None
_SessionLocal: sessionmaker | None = None


def _database_url() -> str:
    return _settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql://", "postgresql+psycopg2://", 1
    )


def get_sync_engine():
    global _sync_engine, _SessionLocal
    if is_mock_database():
        return None
    if _sync_engine is None:
        try:
            _sync_engine = create_engine(_database_url(), pool_pre_ping=True, pool_size=5, max_overflow=10)
            _SessionLocal = sessionmaker(bind=_sync_engine, expire_on_commit=False)
        except Exception:
            _sync_engine = None
            _SessionLocal = None
    return _sync_engine


@contextmanager
def sync_session() -> Iterator[Session]:
    get_sync_engine()
    if _SessionLocal is None:
        raise RuntimeError("PostgreSQL is unavailable")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
