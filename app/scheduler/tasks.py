from datetime import datetime, timedelta
from sqlalchemy import select, and_
from aiogram import Bot

from app.db import async_session
from app.models.models import Event, User
from app.config import config
from app.utils.i18n import L


async def process_reminders():
    """
    Обробляє всі фоні задачі:
    - Автоматично позначає старі події як завершені.
    - Надсилає нагадування користувачам, якщо настав відповідний час.
    - Клонує повторювані події, якщо їх немає на наступну дату.

    Ця функція викликається в циклі планувальника (scheduler).
    """
    now = datetime.now()
    async with async_session() as session:
        bot = Bot(token=config.bot.token)

        # 🔒 Автозавершення подій, що минули понад години тому
        complete_stmt = select(Event).where(
            and_(
                Event.is_done == False,
                Event.time.isnot(None),
                Event.date <= now.date()
            )
        )
        complete_result = await session.execute(complete_stmt)
        to_complete = complete_result.scalars().all()
        for event in to_complete:
            event_datetime = datetime.combine(event.date, event.time)
            if event_datetime < now - timedelta(hours=1):
                event.is_done = True

        # 🔔 Обробка нагадувань
        stmt = select(Event).where(
            and_(
                Event.is_done == False,
                Event.notified == False,
                Event.time.isnot(None),
                Event.remind_before > 0,
            )
        )
        result = await session.execute(stmt)
        events = result.scalars().all()

        for event in events:
            event_datetime = datetime.combine(event.date, event.time)
            notify_at = event_datetime - timedelta(minutes=event.remind_before)

            if notify_at <= now and not event.notified:
                user_result = await session.execute(select(User).where(User.id == event.user_id))
                user = user_result.scalar_one_or_none()
                if user:
                    try:
                        # Побудова повідомлення з урахуванням мови
                        lang = getattr(user, "language", "en")
                        reminder_text = L({
                            "uk": f"🔔 Нагадування!\n<b>{event.title}</b>\n🕒 {event.time.strftime('%H:%M')} сьогодні",
                            "en": f"🔔 Reminder!\n<b>{event.title}</b>\n🕒 {event.time.strftime('%H:%M')} today"
                        }, lang)

                        await bot.send_message(user.telegram_id, reminder_text)
                        event.notified = True

                        # 🔁 Клонування повторюваних подій
                        if event.repeat != "none":
                            next_date = None
                            if event.repeat == "daily":
                                next_date = event.date + timedelta(days=1)
                            elif event.repeat == "weekly":
                                next_date = event.date + timedelta(weeks=1)
                            elif event.repeat == "monthly":
                                try:
                                    next_date = event.date.replace(
                                        month=event.date.month % 12 + 1,
                                        year=event.date.year + (event.date.month // 12)
                                    )
                                except ValueError:
                                    # Уникнення помилок для дат на кшталт 31-го числа
                                    next_date = (event.date.replace(day=1) + timedelta(days=32)).replace(day=1)
                            elif event.repeat == "yearly":
                                try:
                                    next_date = event.date.replace(year=event.date.year + 1)
                                except ValueError:
                                    next_date = event.date + timedelta(days=365)

                            # Якщо аналогічної події ще немає — створити нову
                            if next_date:
                                exists_stmt = select(Event).where(
                                    Event.user_id == event.user_id,
                                    Event.title == event.title,
                                    Event.date == next_date
                                )
                                exists_result = await session.execute(exists_stmt)
                                if not exists_result.scalar_one_or_none():
                                    clone = Event(
                                        user_id=event.user_id,
                                        title=event.title,
                                        date=next_date,
                                        time=event.time,
                                        remind_before=event.remind_before,
                                        category=event.category,
                                        tag=event.tag,
                                        repeat=event.repeat
                                    )
                                    session.add(clone)

                        await session.commit()

                    except Exception as e:
                        print(f"[Reminder] Error sending to {user.telegram_id}: {e}")
