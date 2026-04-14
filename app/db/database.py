from __future__ import annotations

import sqlite3
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.config.settings import get_settings


SQLITE_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_user_id INTEGER NOT NULL UNIQUE,
        first_name TEXT,
        username TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mark_date TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, mark_date),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
)

POSTGRES_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        telegram_user_id BIGINT NOT NULL UNIQUE,
        first_name TEXT,
        username TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_marks (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        mark_date TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, mark_date)
    )
    """,
)


def is_postgres() -> bool:
    return bool(get_settings().database_url)


def sql(query: str) -> str:
    return query.replace("?", "%s") if is_postgres() else query


def get_connection() -> sqlite3.Connection | psycopg.Connection[Any]:
    settings = get_settings()
    if settings.database_url:
        return psycopg.connect(settings.database_url, row_factory=dict_row)

    connection = sqlite3.connect(settings.database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def init_db() -> None:
    settings = get_settings()
    if not settings.database_url:
        settings.database_path.parent.mkdir(parents=True, exist_ok=True)

    schema_statements = POSTGRES_SCHEMA_STATEMENTS if settings.database_url else SQLITE_SCHEMA_STATEMENTS
    with get_connection() as connection:
        for statement in schema_statements:
            connection.execute(statement)
        connection.commit()
