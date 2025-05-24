from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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
    Отримує значення нагадування (в хвилинах) і переходить до категорії.
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
    """
    Отримує теги події (або `-` для пропуску) і запитує тип повтору.
    """
    if message.text == "/cancel":
        return

    tag = message.text.strip()
    await state.update_data(tag=None if tag == "-" else tag)
    await state.set_state(AddEventState.repeat)
    await message.answer(L({
        "uk": (
            "🔁 Повторювання:\n"
            "`none`, `daily`, `weekly`, `monthly`, `yearly`\n"
            "Введи тип повтору:"
        ),
        "en": (
            "🔁 Repeat:\n"
            "`none`, `daily`, `weekly`, `monthly`, `yearly`\n"
            "Enter repeat type:"
        )
    }))


@router.message(AddEventState.repeat)
async def finish_event(message: Message, state: FSMContext):
    """
    Завершує процес додавання події, передаючи управління у відповідну логіку.
    """
    await finish_event_logic(message, state)
