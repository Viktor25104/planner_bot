from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.repositories.user_repo import get_user_by_telegram_id
from app.repositories.event_repo import (
    get_upcoming_events_by_user, get_event_by_id, delete_event
)
from app.utils.i18n import L
from app.db import async_session


async def show_events_for_deletion(message: Message):
    """
    Показує список найближчих подій користувача для видалення з кнопками.

    Якщо користувач не знайдений або подій немає — надсилає відповідне повідомлення.
    """
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(L({
                "uk": "⚠️ Спочатку зареєструйтесь через /start.",
                "en": "⚠️ Please register first via /start."
            }))
            return

        events = await get_upcoming_events_by_user(session, user.id)
        if not events:
            await message.answer(L({
                "uk": "📭 Подій для видалення не знайдено.",
                "en": "📭 No events found for deletion."
            }))
            return

        for event in events:
            time_str = event.time.strftime("%H:%M") if event.time else L({"uk": "без часу", "en": "no time"})
            text = f"<b>{event.title}</b>\n📅 {event.date.strftime('%d.%m.%Y')} о {time_str}"
            button = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=L({"uk": "❌ Видалити", "en": "❌ Delete"}), callback_data=f"delete_event:{event.id}")
            ]])
            await message.answer(text, reply_markup=button)


async def delete_event_by_callback(callback: CallbackQuery, event_id: int):
    """
    Видаляє подію за ID з callback-запиту та оновлює повідомлення користувача.

    Якщо подія вже видалена, надсилає сповіщення.
    """
    async with async_session() as session:
        event = await get_event_by_id(session, event_id)
        if event:
            await delete_event(session, event)
            await callback.message.edit_text(L({
                "uk": f"🗑 Подію <b>{event.title}</b> видалено.",
                "en": f"🗑 Event <b>{event.title}</b> deleted."
            }))
        else:
            await callback.answer(L({
                "uk": "⚠️ Подія вже не існує.",
                "en": "⚠️ Event no longer exists."
            }), show_alert=True)
    await callback.answer()