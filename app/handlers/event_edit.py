from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.utils.i18n import L

from app.services.event_edit_service import (
    list_events_to_edit,
    send_edit_prompt,
    apply_edit
)

router = Router()


class EditEventState(StatesGroup):
    """
    Стани для редагування події:
    - Очікування вибору поля
    - Очікування нового значення
    """
    waiting_for_field = State()
    waiting_for_new_value = State()


@router.message(F.text == "/edit")
async def list_events_for_edit(message: Message, state: FSMContext):
    """
    Обробляє команду /edit.

    Виводить список подій, доступних для редагування.
    """
    await list_events_to_edit(message, state)


@router.callback_query(F.data.startswith("edit_event:"))
async def choose_field(callback: CallbackQuery, state: FSMContext):
    """
    Обробляє вибір події для редагування.

    Зберігає ID події та пропонує вибір поля для редагування.
    """
    event_id = int(callback.data.split(":")[1])
    await state.update_data(event_id=event_id)

    await callback.message.answer(
        L({
            "uk": "🔧 Що ви хочете змінити?",
            "en": "🔧 What would you like to change?"
        }),
        reply_markup=build_edit_keyboard()
    )
    await state.set_state(EditEventState.waiting_for_field)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:"))
async def ask_for_new_value(callback: CallbackQuery, state: FSMContext):
    """
    Обробляє вибір поля для редагування.

    Запитує нове значення.
    """
    await send_edit_prompt(callback, state)
    await state.set_state(EditEventState.waiting_for_new_value)


@router.message(EditEventState.waiting_for_new_value)
async def save_new_value(message: Message, state: FSMContext):
    """
    Отримує нове значення та застосовує зміни до події.
    """
    await apply_edit(message, state)


def build_edit_keyboard():
    """
    Створює клавіатуру для вибору поля редагування події.

    Повертає:
        InlineKeyboardMarkup: клавіатура з кнопками для полів події.
    """
    buttons = [
        [(L({"uk": "Назву", "en": "Title"}), "title"), (L({"uk": "Дату", "en": "Date"}), "date")],
        [(L({"uk": "Час", "en": "Time"}), "time"), (L({"uk": "Нагадування", "en": "Reminder"}), "remind")],
        [(L({"uk": "Категорію", "en": "Category"}), "category"), (L({"uk": "Теги", "en": "Tags"}), "tag")],
        [(L({"uk": "Повторення", "en": "Repeat"}), "repeat")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"edit_field:{code}") for label, code in row]
        for row in buttons
    ])
