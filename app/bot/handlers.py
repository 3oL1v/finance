from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.keyboards import HELP, MARK_DAY, MY_STREAK, OPEN_APP, main_menu
from app.config.settings import get_settings
from app.db.repository import get_current_streak, get_or_create_user, mark_productive_day


router = Router()


def _open_link_markup(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Открыть дашборд", url=url)]]
    )


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    settings = get_settings()
    user = message.from_user
    if user is None:
        return

    get_or_create_user(user.id, first_name=user.first_name, username=user.username)
    text = (
        "Привет! Это <b>Focus Day Bot</b>.\n\n"
        "Бот отмечает продуктивные дни, считает текущую серию и открывает аккуратный Mini App "
        "с личным дашбордом."
    )
    await message.answer(text, reply_markup=main_menu(settings.base_url))


@router.message(Command("help"))
@router.message(F.text == HELP)
async def handle_help(message: Message) -> None:
    settings = get_settings()
    text = (
        "Что умеет бот:\n"
        "• отметить продуктивный день\n"
        "• показать текущую серию\n"
        "• открыть Mini App\n\n"
        f"Текущий адрес Mini App: {settings.base_url}"
    )
    await message.answer(text, reply_markup=main_menu(settings.base_url))


@router.message(Command("streak"))
@router.message(F.text == MY_STREAK)
async def handle_streak(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    streak = get_current_streak(user.id)
    if streak == 0:
        await message.answer(
            "Серия пока не началась. Отметь сегодняшний день и зафиксируй первый шаг."
        )
        return

    await message.answer(f"Твоя текущая серия: <b>{streak}</b> дн.")


@router.message(Command("mark"))
@router.message(F.text == MARK_DAY)
async def handle_mark_day(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    result = mark_productive_day(
        user.id,
        first_name=user.first_name,
        username=user.username,
    )

    if result.inserted:
        text = (
            f"День засчитан. Отличный темп.\n"
            f"Текущая серия: <b>{result.streak}</b> дн."
        )
    else:
        text = (
            f"Сегодняшний день уже отмечен.\n"
            f"Текущая серия: <b>{result.streak}</b> дн."
        )

    await message.answer(text)


@router.message(F.text == OPEN_APP)
async def handle_open_app(message: Message) -> None:
    settings = get_settings()
    if settings.base_url.startswith("https://"):
        await message.answer(
            "Открывай Mini App и смотри свой ритм дня.",
            reply_markup=_open_link_markup(settings.base_url),
        )
        return

    await message.answer(
        "Mini App в Telegram открывается только по HTTPS. Ниже даю обычную ссылку для браузера.",
        reply_markup=_open_link_markup(settings.base_url),
    )
