from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.db import async_session
from app.repositories.event_repo import get_events_in_range
from app.repositories.user_repo import get_user_by_telegram_id
from app.services.event_add_service import (
    validate_date, validate_time, finish_event_logic
)
from app.utils.i18n import L

router = Router()


class AddEventState(StatesGroup):
    """
    Клас, що описує стани FSM при додаванні події.
    """
    title = State()
    date = State()
    time = State()
    remind = State()
    category = State()
    tag = State()
    repeat = State()


@router.message(F.text == "/add")
async def cmd_add(message: Message, state: FSMContext):
    """
    Обробник команди /add. Ініціалізує додавання події з введення назви.
    """
    await state.set_state(AddEventState.title)
    await message.answer(L({
        "uk": "📝 Введи назву події:",
        "en": "📝 Enter event title:"
    }))


@router.message(AddEventState.title)
async def add_title(message: Message, state: FSMContext):
    """
    Отримує назву події та переходить до введення дати.
    """
    await state.update_data(title=message.text.strip())
    await state.set_state(AddEventState.date)
    await message.answer(L({
        "uk": "📅 Введи дату події у форматі ДД.ММ.РРРР:",
        "en": "📅 Enter event date (DD.MM.YYYY):"
    }))


@router.message(AddEventState.date)
async def add_date(message: Message, state: FSMContext):
    """
    Обробляє введену дату події. У разі помилки просить повторити введення.
    """
    if message.text in ["/cancel", "/today", "/start", "/help"]:
        await state.clear()
        return

    try:
        parsed_date = validate_date(message.text)
        await state.update_data(date=parsed_date)
        await state.set_state(AddEventState.time)
        await message.answer(L({
            "uk": "⏰ Введи час події у форматі ГГ:ХХ (24-год):",
            "en": "⏰ Enter event time (HH:MM, 24h):"
        }))
    except ValueError:
        await message.answer(L({
            "uk": "❌ Невірний формат дати. Спробуй ще раз: ДД.ММ.РРРР",
            "en": "❌ Invalid date format. Try again: DD.MM.YYYY"
        }))


@router.message(AddEventState.time)
async def add_time(message: Message, state: FSMContext):
    """
    Обробляє введений час події. У разі помилки просить повторити.
    """
    if message.text == "/cancel":
        return

    try:
        parsed_time = validate_time(message.text)
        await state.update_data(time=parsed_time)
        await state.set_state(AddEventState.remind)
        await message.answer(L({
            "uk": "🔔 За скільки хвилин до події надіслати нагадування?",
            "en": "🔔 How many minutes before the event to send a reminder?"
        }))
    except ValueError:
        await message.answer(L({
            "uk": "❌ Невірний формат часу. Спробуй ще раз: ГГ:ХХ",
            "en": "❌ Invalid time format. Try again: HH:MM"
        }))


@router.message(AddEventState.remind)
async def add_category(message: Message, state: FSMContext):
    """
    Отримує кількість хвилин до нагадування і переводить FSM у стан введення категорії.
    """
    if message.text == "/cancel":
        return

    try:
        remind = int(message.text.strip())
        await state.update_data(remind_before=remind)
        await state.set_state(AddEventState.category)
        await message.answer(L({
            "uk": "🏷 Категорія (або `-`):",
            "en": "🏷 Category (or `-`):"
        }))
    except ValueError:
        await message.answer(L({
            "uk": "❌ Введи лише число (хвилини до події)",
            "en": "❌ Please enter a number (minutes before event)"
        }))


@router.message(AddEventState.category)
async def add_tag(message: Message, state: FSMContext):
    """
    Отримує категорію події (або `-` для пропуску) і переходить до тегів.
    """
    if message.text == "/cancel":
        return

    category = message.text.strip()
    await state.update_data(category=None if category == "-" else category)
    await state.set_state(AddEventState.tag)
    await message.answer(L({
        "uk": "🔖 Теги (через кому або `-`):",
        "en": "🔖 Tags (comma separated or `-`):"
    }))


@router.message(AddEventState.tag)
async def ask_repeat(message: Message, state: FSMContext):
    if message.text == "/cancel":
        return

    tag = message.text.strip()
    await state.update_data(tag=None if tag == "-" else tag)
    await state.set_state(AddEventState.repeat)

    lang = "uk" if message.from_user.language_code == "uk" else "en"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔁 Без повтору" if lang == "uk" else "🔁 None")],
            [KeyboardButton(text="📆 Щодня" if lang == "uk" else "📆 Daily")],
            [KeyboardButton(text="📅 Щотижня" if lang == "uk" else "📅 Weekly")],
            [KeyboardButton(text="📇 Щомісяця" if lang == "uk" else "📇 Monthly")],
            [KeyboardButton(text="🗓 Щороку" if lang == "uk" else "🗓 Yearly")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        L({
            "uk": "🔁 Обери тип повтору:",
            "en": "🔁 Choose repeat type:"
        }),
        reply_markup=keyboard
    )


@router.message(AddEventState.repeat)
async def finish_event(message: Message, state: FSMContext):
    """
    Завершує процес додавання події. Перевіряє конфлікти в часі,
    зберігає дані FSM і запускає логіку збереження або запит підтвердження.
    """
    REPEAT_MAP = {
        "🔁 Без повтору": "none",
        "📆 Щодня": "daily",
        "📅 Щотижня": "weekly",
        "📇 Щомісяця": "monthly",
        "🗓 Щороку": "yearly",
        "🔁 None": "none",
        "📆 Daily": "daily",
        "📅 Weekly": "weekly",
        "📇 Monthly": "monthly",
        "🗓 Yearly": "yearly"
    }

    raw_repeat = message.text.strip()
    repeat = REPEAT_MAP.get(raw_repeat)

    if not repeat:
        await message.answer(L({
            "uk": "❌ Обери варіант з кнопок.",
            "en": "❌ Please choose from the buttons."
        }))
        return

    await state.update_data(repeat=repeat)
    data = await state.get_data()

    event_datetime = datetime.combine(data["date"], data["time"])
    start = event_datetime - timedelta(minutes=15)
    end = event_datetime + timedelta(minutes=15)

    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        nearby_events = await get_events_in_range(session, user.id, start.date(), end.date())

    overlapping = [
        e for e in nearby_events if abs(
            datetime.combine(e.date, e.time) - event_datetime
        ).total_seconds() < 15 * 60
    ]

    if overlapping:
        events_text = "\n".join(
            f"• {e.title} ({e.date.strftime('%d.%m')} {e.time.strftime('%H:%M')})" for e in overlapping)
        await state.set_state("confirm_conflict")
        await state.update_data(event_data=data)

        await message.answer(L({
            "uk": f"⚠️ У цей час вже є події:\n{events_text}\n\nДодати подію попри це? (так/ні)",
            "en": f"⚠️ There are already events near this time:\n{events_text}\n\nAdd anyway? (yes/no)"
        }))
    else:
        await finish_event_logic(message, state)
