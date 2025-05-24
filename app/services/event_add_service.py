from datetime import datetime
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from app.db import async_session
from app.models.models import User, Event
from app.utils.i18n import L


def validate_date(text: str) -> datetime.date:
    """
    Перетворює рядок у форматі 'ДД.ММ.РРРР' на об'єкт дати.

    Args:
        text (str): Рядок з датою.

    Returns:
        datetime.date: Парсена дата.
    """
    return datetime.strptime(text.strip(), "%d.%m.%Y").date()


def validate_time(text: str) -> datetime.time:
    """
    Перетворює рядок у форматі 'ГГ:ХХ' на об'єкт часу.

    Args:
        text (str): Рядок з часом.

    Returns:
        datetime.time: Парсений час.
    """
    return datetime.strptime(text.strip(), "%H:%M").time()


async def finish_event_logic(message: Message, state: FSMContext):
    """
    Завершує процес додавання події:
    - Перевіряє формат повторення.
    - Зберігає подію в базу.
    - Надає рекомендації (якщо багато подій або вони перекриваються).

    Args:
        message (Message): Повідомлення користувача.
        state (FSMContext): Контекст FSM.

    Returns:
        Підтвердження збереження та рекомендації (якщо є).
    """
    data = await state.get_data()
    lang = message.from_user.language_code if message.from_user.language_code in ("uk", "en") else "uk"

    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(L({
                "uk": "⚠️ Користувача не знайдено. Напишіть /start.",
                "en": "⚠️ User not found. Please send /start."
            }))
            return

        event = Event(
            user_id=user.id,
            title=data["title"],
            date=data["date"],
            time=data["time"],
            remind_before=data["remind_before"],
            category=data.get("category"),
            tag=data.get("tag"),
            repeat=data.get("repeat"),
        )
        session.add(event)
        await session.commit()

        stmt_day = select(Event).where(Event.user_id == user.id, Event.date == event.date)
        day_result = await session.execute(stmt_day)
        same_day_events = day_result.scalars().all()

        recommendations = []

        if len(same_day_events) >= 5:
            recommendations.append(L({
                "uk": "⚠️ У вас вже багато подій на цей день. Можливо, варто щось перенести.",
                "en": "⚠️ You already have many events on this day. Consider rescheduling some."
            }))

        for other in same_day_events:
            if other.id == event.id or not other.time or not event.time:
                continue
            delta = abs((datetime.combine(event.date, event.time) - datetime.combine(other.date,
                                                                                     other.time)).total_seconds()) / 60
            if 0 < delta < 30:
                recommendations.append(L({
                    "uk": "⏱ Події йдуть майже без перерв.",
                    "en": "⏱ Events are scheduled almost back-to-back."
                }))
                break

        if event.repeat != "none":
            existing = [e for e in same_day_events if e.time == event.time and e.repeat == event.repeat]
            if len(existing) > 1:
                recommendations.append(L({
                    "uk": "🔁 Уже є така повторювана подія.",
                    "en": "🔁 There is already such a recurring event."
                }))

    await state.clear()
    from app.handlers.event_menu import build_main_menu
    await message.answer(L({
        "uk": "✅ Подію збережено з усіма параметрами!",
        "en": "✅ Event saved with all parameters!"
    }), reply_markup=build_main_menu(lang))

    if recommendations:
        await message.answer(L({
            "uk": "📌 <b>Поради:</b>\n" + "\n".join(recommendations),
            "en": "📌 <b>Recommendations:</b>\n" + "\n".join(recommendations)
        }))

    # Експорт в Google Calendar
    from app.services.event_list_service import export_one_to_google
    await export_one_to_google(message, event.id)