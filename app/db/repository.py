from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.db.database import get_connection, is_postgres, sql


UTC = timezone.utc
DEMO_OFFSETS = (1, 2, 3, 5)


@dataclass(frozen=True)
class DayMarkResult:
    inserted: bool
    streak: int


def _utc_now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def get_or_create_user(
    telegram_user_id: int,
    first_name: str | None = None,
    username: str | None = None,
) -> dict[str, Any]:
    with get_connection() as connection:
        row = connection.execute(
            sql(
                """
            SELECT id, telegram_user_id, first_name, username, created_at
            FROM users
            WHERE telegram_user_id = ?
            """,
            ),
            (telegram_user_id,),
        ).fetchone()

        if row is None:
            connection.execute(
                sql(
                    """
                INSERT INTO users (telegram_user_id, first_name, username, created_at)
                VALUES (?, ?, ?, ?)
                """,
                ),
                (telegram_user_id, first_name or "", username or "", _utc_now_iso()),
            )
            connection.commit()
        else:
            connection.execute(
                sql(
                    """
                UPDATE users
                SET first_name = ?, username = ?
                WHERE telegram_user_id = ?
                """,
                ),
                (first_name or row["first_name"], username or row["username"], telegram_user_id),
            )
            connection.commit()

        row = connection.execute(
            sql(
                """
            SELECT id, telegram_user_id, first_name, username, created_at
            FROM users
            WHERE telegram_user_id = ?
            """,
            ),
            (telegram_user_id,),
        ).fetchone()

        ensure_demo_history(connection, row["id"])
        return dict(row)


def ensure_demo_history(connection, user_id: int) -> None:
    existing = connection.execute(
        sql("SELECT COUNT(*) AS total FROM daily_marks WHERE user_id = ?"),
        (user_id,),
    ).fetchone()
    if existing is not None and existing["total"] > 0:
        return

    today = date.today()
    rows = [
        (user_id, (today - timedelta(days=offset)).isoformat(), _utc_now_iso())
        for offset in DEMO_OFFSETS
    ]
    insert_sql = (
        """
        INSERT INTO daily_marks (user_id, mark_date, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT (user_id, mark_date) DO NOTHING
        """
        if is_postgres()
        else """
        INSERT OR IGNORE INTO daily_marks (user_id, mark_date, created_at)
        VALUES (?, ?, ?)
        """
    )
    if is_postgres():
        with connection.cursor() as cursor:
            cursor.executemany(sql(insert_sql), rows)
    else:
        connection.executemany(sql(insert_sql), rows)
    connection.commit()


def mark_productive_day(
    telegram_user_id: int,
    first_name: str | None = None,
    username: str | None = None,
) -> DayMarkResult:
    user = get_or_create_user(telegram_user_id, first_name=first_name, username=username)
    with get_connection() as connection:
        cursor = connection.execute(
            sql(
                """
                INSERT INTO daily_marks (user_id, mark_date, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT (user_id, mark_date) DO NOTHING
                """
                if is_postgres()
                else """
                INSERT OR IGNORE INTO daily_marks (user_id, mark_date, created_at)
                VALUES (?, ?, ?)
                """,
            ),
            (user["id"], date.today().isoformat(), _utc_now_iso()),
        )
        connection.commit()

    return DayMarkResult(
        inserted=cursor.rowcount > 0,
        streak=get_current_streak(telegram_user_id),
    )


def get_marked_dates(
    telegram_user_id: int,
    start_date: date,
    end_date: date,
) -> set[date]:
    user = get_or_create_user(telegram_user_id)
    with get_connection() as connection:
        rows = connection.execute(
            sql(
                """
            SELECT mark_date
            FROM daily_marks
            WHERE user_id = ? AND mark_date BETWEEN ? AND ?
            ORDER BY mark_date ASC
            """,
            ),
            (user["id"], start_date.isoformat(), end_date.isoformat()),
        ).fetchall()

    return {date.fromisoformat(str(row["mark_date"])) for row in rows}


def get_current_streak(telegram_user_id: int) -> int:
    user = get_or_create_user(telegram_user_id)
    with get_connection() as connection:
        rows = connection.execute(
            sql("SELECT mark_date FROM daily_marks WHERE user_id = ? ORDER BY mark_date DESC"),
            (user["id"],),
        ).fetchall()

    marked_dates = {date.fromisoformat(str(row["mark_date"])) for row in rows}
    today = date.today()

    if today in marked_dates:
        cursor_day = today
    elif (today - timedelta(days=1)) in marked_dates:
        cursor_day = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor_day in marked_dates:
        streak += 1
        cursor_day -= timedelta(days=1)

    return streak


def was_marked_today(telegram_user_id: int) -> bool:
    today = date.today()
    return today in get_marked_dates(telegram_user_id, today, today)
