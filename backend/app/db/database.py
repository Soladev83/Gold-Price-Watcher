"""
Database engine and session factory.
Supports both SQLite (local dev) and PostgreSQL/Supabase (production).
DATABASE_URL is read from the environment; defaults to a local SQLite file.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "sqlite:///./gold_watcher.db",   # safe local default
)

# SQLite needs check_same_thread=False; ignored for Postgres
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't already exist."""
    from app.db.models import Base  # noqa: F401 — ensures models are registered
    Base.metadata.create_all(bind=engine)
