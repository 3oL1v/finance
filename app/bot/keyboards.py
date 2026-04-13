from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo


OPEN_APP = "Открыть Mini App"
MARK_DAY = "Отметить продуктивный день"
MY_STREAK = "Моя серия"
HELP = "Помощь"


def main_menu(base_url: str) -> ReplyKeyboardMarkup:
    mini_app_button = (
        KeyboardButton(text=OPEN_APP, web_app=WebAppInfo(url=base_url))
        if base_url.startswith("https://")
        else KeyboardButton(text=OPEN_APP)
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [mini_app_button],
            [KeyboardButton(text=MARK_DAY), KeyboardButton(text=MY_STREAK)],
            [KeyboardButton(text=HELP)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие",
    )
