from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select
from app.db import async_session
from app.handlers.event_add import cmd_add

from app.handlers.event_chart import chart_handler
from app.handlers.event_export import export_csv
from app.handlers.event_list import list_today, list_week
from app.handlers.event_stats import stats_handler
from app.integrations.google_calendar import import_events_from_google
from app.models.models import User
from app.repositories.user_repo import get_user_by_telegram_id
from app.utils.i18n import get_switch_lang, get_lang_button
from app.utils.i18n import L

router = Router()


def build_main_menu(lang: str = "uk") -> ReplyKeyboardMarkup:
    """
    Створює клавіатуру головного меню з урахуванням мови користувача.

    Args:
        lang (str): 'uk' або 'en' — мова для кнопок.

    Returns:
        ReplyKeyboardMarkup: розмітка клавіатури.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Додати" if lang == "uk" else "➕ Add")],
            [
                KeyboardButton(text="📅 Сьогодні" if lang == "uk" else "📅 Today"),
                KeyboardButton(text="🗓 Тиждень" if lang == "uk" else "🗓 Week")
            ],
            [
                KeyboardButton(text="📤 CSV" if lang == "uk" else "📤 CSV"),
                KeyboardButton(text="📥 Google" if lang == "uk" else "📥 Google")
            ],
            [
                KeyboardButton(text="📈 Статистика" if lang == "uk" else "📈 Stats"),
                KeyboardButton(text="📊 Графік" if lang == "uk" else "📊 Chart")
            ],
            [KeyboardButton(text=get_lang_button(lang))]
        ],
        input_field_placeholder="Меню ↓" if lang == "uk" else "Menu ↓"
    )


@router.message(F.text == "/menu")
async def send_menu(message: Message):
    """
    Обробляє команду /menu.

    Відображає для користувача головне меню з урахуванням його мови.
    """
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        lang = user.language if user else "uk"
        await message.answer(
            "📋 Меню доступне нижче 👇" if lang == "uk" else "📋 Menu below 👇",
            reply_markup=build_main_menu(lang)
        )


@router.message(F.text.in_(["🇬🇧 English", "🇺🇦 Українська"]))
async def switch_language(message: Message):
    """
    Змінює мову інтерфейсу користувача.

    Визначає поточну мову і перемикає на іншу (uk <-> en).
    """
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("⚠️ Спочатку зареєструйтесь через /start.")
            return

        new_lang = get_switch_lang(user.language)
        user.language = new_lang
        await session.commit()

        await message.answer(
            "✅ Мову змінено!" if new_lang == "uk" else "✅ Language switched!",
            reply_markup=build_main_menu(new_lang)
        )


@router.message(F.text.in_(["➕ Додати", "➕ Add"]))
async def menu_add_event(message: Message, state: FSMContext):
    """
    Обробляє кнопку "Додати подію".

    Запускає FSM для створення нової події.
    """
    await cmd_add(message, state)


@router.message(F.text.in_(["📅 Сьогодні", "📅 Today"]))
async def menu_today(message: Message):
    """
    Обробляє кнопку "Сьогодні".

    Виводить список подій на поточний день.
    """
    await list_today(message)


@router.message(F.text.in_(["🗓 Тиждень", "🗓 Week"]))
async def menu_week(message: Message):
    """
    Обробляє кнопку "Тиждень".

    Виводить список подій на поточний тиждень.
    """
    await list_week(message)


@router.message(F.text.in_(["📤 CSV", "📤 CSV"]))
async def menu_export_csv(message: Message):
    """
    Обробляє кнопку "Експорт CSV".

    Надсилає файл з подіями у форматі CSV.
    """
    await export_csv(message)


@router.message(F.text.in_(["📥 Google", "📥 Google"]))
async def menu_import_google(message: Message):
    """
    Обробляє кнопку "Імпорт Google".

    Імпортує події з Google Calendar.
    """
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("⚠️ Спочатку зареєструйтесь через /start.")
            return

        try:
            count = await import_events_from_google(user)
            await message.answer(L({
                "uk": f"✅ Імпортовано {count} подій з Google Календаря.",
                "en": f"✅ Imported {count} events from Google Calendar."
            }, user.language))
        except Exception as e:
            print(f"[Import Error] {e}")
            await message.answer(L({
                "uk": "❌ Помилка при імпорті з Google.",
                "en": "❌ Failed to import from Google."
            }, user.language))


@router.message(F.text.in_(["📈 Статистика", "📈 Stats"]))
async def menu_stats(message: Message):
    """
    Обробляє кнопку "Статистика".

    Виводить статистичний звіт користувача.
    """
    await stats_handler(message)


@router.message(F.text.in_(["📊 Графік", "📊 Chart"]))
async def menu_chart(message: Message):
    """
    Обробляє кнопку "Графік".

    Виводить графік активності або категорій.
    """
    await chart_handler(message)
