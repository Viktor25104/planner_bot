from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from app.db import async_session
from app.models.models import Event
from app.repositories.user_repo import get_user_by_telegram_id
from app.repositories.event_repo import get_today_user_events, mark_event_as_done, get_event_by_id

router = Router()

def simple_format_event(event: Event) -> str:
    """
    Форматує подію у вигляді повідомлення для Telegram.

    Args:
        event (Event): Об'єкт події.

    Returns:
        str: Відформатований рядок для відправки користувачу.
    """
    lines = [
        f"<b>{event.title}</b>",
        f"🗓 {event.date.strftime('%d.%m.%Y')} о {event.time.strftime('%H:%M') if event.time else 'без часу'}"
    ]
    if event.category:
        lines.append(f"🏷 Категорія: {event.category}")
    if event.tag:
        lines.append(f"🔖 Теги: {event.tag}")
    if event.is_done:
        lines.append("✅ Виконано")
    return "\n".join(lines)


@router.message(F.text.startswith("/done"))
async def show_today_events_to_mark_done(message: Message):
    """
    Обробляє команду /done. Виводить список сьогоднішніх подій, які вже відбулися,
    і дозволяє позначити їх як виконані за допомогою кнопки.

    Args:
        message (Message): Об'єкт повідомлення Telegram.
    """
    today = datetime.now().date()

    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("⚠️ Ви ще не зареєстровані. Напишіть /start.")
            return

        events = await get_today_user_events(session, user.id, today)

        if not events:
            await message.answer("📭 Немає подій на сьогодні, які можна відзначити як виконані.")
            return

        for event in events:
            await message.answer(
                simple_format_event(event),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="✅ Виконано", callback_data=f"done:{event.id}")
                ]])
            )


@router.callback_query(F.data.startswith("done:"))
async def mark_event_done_callback(callback: CallbackQuery):
    """
    Обробляє натискання кнопки "✅ Виконано". Позначає відповідну подію як виконану,
    якщо вона належить поточному користувачу.

    Args:
        callback (CallbackQuery): Callback-запит від користувача Telegram.
    """
    event_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.answer("⚠️ Подія не знайдена або не належить вам.", show_alert=True)
            return

        success = await mark_event_as_done(session, event_id, user.id)

        if not success:
            await callback.answer("⚠️ Подія не знайдена або не належить вам.", show_alert=True)
            return

        event = await get_event_by_id(session, event_id)

        await callback.message.edit_text(
            f"✅ <b>Позначено як виконане:</b>\n{simple_format_event(event)}",
            parse_mode="HTML"
        )
        await callback.answer("✅ Виконано.")
