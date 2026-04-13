from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta

from app.db.repository import get_current_streak, get_marked_dates, get_or_create_user, was_marked_today


DEMO_USER_ID = 770001
TASK_POOL = [
    ("Подготовить главный фокус на день", "Планирование"),
    ("Закрыть самую важную задачу без отвлечений", "Deep work"),
    ("Отключить лишние уведомления на время работы", "Концентрация"),
    ("Сделать 45 минут без переключений", "Режим"),
    ("Провести короткий вечерний обзор", "Рефлексия"),
    ("Освободить утро под ключевую задачу", "Приоритет"),
]
QUOTES = [
    ("Маленький ритм сильнее редкого вдохновения.", "Focus Day"),
    ("Сначала важное. Остальное потом.", "Focus Day"),
    ("Продуктивность любит ясность и повторяемость.", "Focus Day"),
    ("Один завершенный фокус лучше десяти начатых дел.", "Focus Day"),
    ("Спокойный темп часто побеждает суету.", "Focus Day"),
]
DAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def _seed_int(*parts: object) -> int:
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _pick_tasks(user_id: int, today_marked: bool) -> list[dict[str, object]]:
    rng = random.Random(_seed_int(user_id, date.today().isoformat(), "tasks"))
    selected = rng.sample(TASK_POOL, k=3)
    completed_count = 2 if today_marked else 1

    return [
        {"title": title, "category": category, "done": index < completed_count}
        for index, (title, category) in enumerate(selected)
    ]


def _pick_quote(user_id: int) -> dict[str, str]:
    index = _seed_int(user_id, date.today().isoformat(), "quote") % len(QUOTES)
    text, author = QUOTES[index]
    return {"text": text, "author": author}


def _plural_days(value: int) -> str:
    if value % 10 == 1 and value % 100 != 11:
        return "день"
    if value % 10 in {2, 3, 4} and value % 100 not in {12, 13, 14}:
        return "дня"
    return "дней"


def build_dashboard_data(
    telegram_user_id: int | None = None,
    first_name: str | None = None,
    username: str | None = None,
) -> dict[str, object]:
    resolved_user_id = telegram_user_id or DEMO_USER_ID
    fallback_name = first_name or "друг"
    user = get_or_create_user(resolved_user_id, first_name=fallback_name, username=username)

    today = date.today()
    week_start = today - timedelta(days=6)
    marked_dates = get_marked_dates(resolved_user_id, week_start, today)
    today_marked = was_marked_today(resolved_user_id)
    streak = get_current_streak(resolved_user_id)
    progress_percent = round(len(marked_dates) / 7 * 100)
    productive_days = len(marked_dates)
    display_name = (user.get("first_name") or fallback_name or "друг").strip()

    week_activity = []
    for offset in range(6, -1, -1):
        current_day = today - timedelta(days=offset)
        week_activity.append(
            {
                "label": DAY_LABELS[current_day.weekday()],
                "iso_date": current_day.isoformat(),
                "day_number": current_day.day,
                "completed": current_day in marked_dates,
                "is_today": current_day == today,
            }
        )

    if today_marked:
        summary_title = "Сегодня уже засчитан"
        summary_text = "День отмечен. Сохрани темп и закрой главный фокус без суеты."
        hero_badge = "Ритм зафиксирован"
    else:
        summary_title = "Остался один шаг"
        summary_text = "Отметь продуктивный день в боте или прямо в Mini App, чтобы продлить серию."
        hero_badge = "Хороший темп недели"

    return {
        "user_id": resolved_user_id,
        "demo_mode": resolved_user_id == DEMO_USER_ID,
        "greeting": f"Твой продуктивный день, {display_name}",
        "hero_subtitle": "Минималистичный трекер фокуса с аккуратным ритмом, серией и наглядной неделей.",
        "hero_badge": hero_badge,
        "today_marked": today_marked,
        "streak": streak,
        "streak_label": f"{streak} {_plural_days(streak)}",
        "progress_percent": progress_percent,
        "progress_label": f"{productive_days} из 7 дней активны",
        "week_activity": week_activity,
        "tasks": _pick_tasks(resolved_user_id, today_marked=today_marked),
        "quote": _pick_quote(resolved_user_id),
        "summary": {"title": summary_title, "text": summary_text},
        "stats": [
            {"label": "Активных дней", "value": f"{productive_days}/7"},
            {"label": "Текущая серия", "value": f"{streak} {_plural_days(streak)}"},
            {"label": "Прогресс недели", "value": f"{progress_percent}%"},
        ],
    }
