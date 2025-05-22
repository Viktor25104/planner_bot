from datetime import datetime
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.repositories.user_repo import get_user_by_telegram_id
from app.repositories.event_repo import get_events_by_user, get_event_by_id, save_event
from app.utils.i18n import L
from app.db import async_session


edit_prompts = {
    "title": L({
        "uk": "✏️ Введіть нову назву події:",
        "en": "✏️ Enter new event title:"
    }),
    "date": L({
        "uk": "📅 Введіть нову дату (ДД.ММ.РРРР):",
        "en": "📅 Enter new date (DD.MM.YYYY):"
    }),
    "time": L({
        "uk": "⏰ Введіть новий час (ГГ:ХХ):",
        "en": "⏰ Enter new time (HH:MM):"
    }),
    "remind": L({
        "uk": "🔔 За скільки хвилин до події надіслати нагадування?",
        "en": "🔔 How many minutes before the event to send a reminder?"
    }),
    "category": L({
        "uk": "🏷 Введіть нову категорію, або `-` для очищення:",
        "en": "🏷 Enter new category or `-` to clear:"
    }),
    "tag": L({
        "uk": "🔖 Введіть нові теги (через кому), або `-` для очищення:",
        "en": "🔖 Enter new tags (comma separated) or `-` to clear:"
    }),
    "repeat": L({
        "uk": "🔁 Напишіть тип повторення: none / daily / weekly / monthly / yearly",
        "en": "🔁 Enter repeat type: none / daily / weekly / monthly / yearly"
    }),
}


async def list_events_to_edit(message: Message, state: FSMContext):
    """
    Виводить список подій користувача з кнопками для редагування.

    Якщо користувача або подій немає — показує відповідне повідомлення.
    """
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(L({
                "uk": "⚠️ Спочатку зареєструйтесь через /start.",
                "en": "⚠️ Please register first via /start."
            }))
            return

        events = await get_events_by_user(session, user.id)
        if not events:
            await message.answer(L({
                "uk": "📭 У вас ще немає подій.",
                "en": "📭 You have no events yet."
            }))
            return

        for event in events:
            date_str = event.date.strftime("%d.%m.%Y")
            time_str = event.time.strftime("%H:%M") if event.time else L({"uk": "без часу", "en": "no time"})
            text = f"<b>{event.title}</b>\n📅 {date_str} о {time_str}"

            buttons = [
                InlineKeyboardButton(text=L({"uk": "✏️ Редагувати", "en": "✏️ Edit"}),
                                     callback_data=f"edit_event:{event.id}")
            ]
            await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[buttons]))


async def send_edit_prompt(callback: CallbackQuery, state: FSMContext):
    """
    Виводить запит на введення нового значення для вказаного поля.
    """
    field = callback.data.split(":")[1]
    await state.update_data(field=field)

    lang = getattr(callback.from_user, "language_code", "en")
    prompt_text = edit_prompts[field]
    if callable(prompt_text):
        prompt_text = prompt_text(lang)

    await callback.message.answer(prompt_text)
    await callback.answer()


async def apply_edit(message: Message, state: FSMContext):
    """
    Застосовує редагування обраного поля події.

    У разі помилки формату або недійсного значення надсилає відповідне повідомлення.
    """
    data = await state.get_data()
    event_id = data.get("event_id")
    field = data.get("field")
    value = message.text.strip()

    async with async_session() as session:
        event = await get_event_by_id(session, event_id)
        if not event:
            await message.answer(L({"uk": "⚠️ Подія не знайдена.", "en": "⚠️ Event not found."}))
            await state.clear()
            return

        try:
            if field == "title":
                event.title = value
            elif field == "date":
                event.date = datetime.strptime(value, "%d.%m.%Y").date()
            elif field == "time":
                event.time = datetime.strptime(value, "%H:%M").time()
            elif field == "remind":
                event.remind_before = int(value)
            elif field == "category":
                event.category = None if value == "-" else value
            elif field == "tag":
                event.tag = None if value == "-" else value
            elif field == "repeat":
                if value.lower() not in ("none", "daily", "weekly", "monthly", "yearly"):
                    await message.answer(L({
                        "uk": "❌ Невірне значення повтору.",
                        "en": "❌ Invalid repeat value."
                    }))
                    return
                event.repeat = value.lower()
            else:
                await message.answer(L({
                    "uk": "⚠️ Невідома дія.",
                    "en": "⚠️ Unknown action."
                }))
                await state.clear()
                return

            await save_event(session, event)
            await message.answer(L({
                "uk": "✅ Подію оновлено.",
                "en": "✅ Event updated."
            }))
        except Exception:
            await message.answer(L({
                "uk": "❌ Невірний формат. Спробуйте ще раз.",
                "en": "❌ Invalid format. Please try again."
            }))

    await state.clear()
