"""Database connection management."""

from __future__ import annotations

import os

import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import Engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/network_graph",
)

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = sqlalchemy.create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


def query_df(sql: str, params: dict | None = None):
    """Execute SQL and return as pandas DataFrame."""
    import pandas as pd
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        columns = list(result.keys())
        rows = result.fetchall()
    return pd.DataFrame(rows, columns=columns)


def execute(sql: str, params: dict | None = None) -> None:
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(sql), params or {})
        conn.commit()
