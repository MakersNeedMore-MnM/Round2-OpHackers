"""
SQLite persistence via SQLModel. File-based, zero-setup, demo-safe.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

_DB_PATH = Path(__file__).resolve().parent / "orca_runs.db"
SQLITE_URL = os.environ.get("ORCA_DB_URL", f"sqlite:///{_DB_PATH}")

engine = create_engine(SQLITE_URL, echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    """Create tables if missing. Safe to call on every startup."""
    import models  # noqa: F401
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency yielding a short-lived session."""
    with Session(engine) as session:
        yield session
