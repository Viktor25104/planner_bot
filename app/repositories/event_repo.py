from sqlalchemy import select, and_
from datetime import date, timedelta, time, datetime
from app.models.models import Event


async def get_event_by_id(session, event_id: int):
    """
    Отримує подію за її унікальним ID.

    Args:
        session: Активна сесія SQLAlchemy.
        event_id (int): ID події.

    Returns:
        Event | None: Подія або None, якщо не знайдено.
    """
    result = await session.execute(select(Event).where(Event.id == event_id))
    return result.scalar_one_or_none()


async def get_events_by_user(session, user_id: int, ordered: bool = False):
    """
    Отримує всі події користувача.

    Args:
        session: Активна сесія SQLAlchemy.
        user_id (int): ID користувача.
        ordered (bool): Чи сортувати події за датою і часом.

    Returns:
        List[Event]: Список подій користувача.
    """
    stmt = select(Event).where(Event.user_id == user_id)
    if ordered:
        stmt = stmt.order_by(Event.date, Event.time)

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_upcoming_events_by_user(session, user_id: int, days_ahead: int = 7):
    """
    Отримує майбутні події користувача на вказану кількість днів наперед.

    Args:
        session: Активна сесія SQLAlchemy.
        user_id (int): ID користувача.
        days_ahead (int): Кількість днів наперед для фільтрації.

    Returns:
        List[Event]: Список майбутніх подій.
    """
    today = date.today()
    limit_day = today + timedelta(days=days_ahead)

    stmt = select(Event).where(
        and_(
            Event.user_id == user_id,
            Event.date >= today,
            Event.date <= limit_day
        )
    ).order_by(Event.date, Event.time)

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_events_in_range(session, user_id: int, start: date, end: date, category=None, tag=None):
    """
    Отримує події у вказаному діапазоні дат з фільтрами за категорією і тегом.

    Args:
        session: Активна сесія SQLAlchemy.
        user_id (int): ID користувача.
        start (date): Початкова дата.
        end (date): Кінцева дата.
        category (str | None): Категорія для фільтрації.
        tag (str | None): Тег для фільтрації.

    Returns:
        List[Event]: Відфільтровані події.
    """
    filters = [
        Event.user_id == user_id,
        Event.date >= start,
        Event.date <= end
    ]
    if category:
        filters.append(Event.category.ilike(f"%{category}%"))
    if tag:
        filters.append(Event.tag.ilike(f"%{tag}%"))

    result = await session.execute(
        select(Event).where(and_(*filters)).order_by(Event.date, Event.time)
    )
    return result.scalars().all()


async def get_today_user_events(session, user_id: int, date: date, only_past: bool = True):
    """
    Отримує події користувача на конкретну дату. За замовчуванням лише ті, що вже пройшли.

    Args:
        session: Активна сесія SQLAlchemy.
        user_id (int): ID користувача.
        date (date): Дата, на яку фільтрувати події.
        only_past (bool): Якщо True — лише ті, що були раніше поточного часу.

    Returns:
        List[Event]: Список подій.
    """
    stmt = select(Event).where(
        Event.user_id == user_id,
        Event.date == date,
        Event.is_done == False
    )
    result = await session.execute(stmt)
    events = result.scalars().all()

    if only_past:
        now_time = datetime.now().time()
        return [e for e in events if e.time and e.time <= now_time]

    return events


async def exists_event(session, user_id: int, title: str, date: date, time: time) -> bool:
    """
    Перевіряє, чи існує подія з таким самим заголовком, датою і часом у користувача.

    Args:
        session: Активна сесія SQLAlchemy.
        user_id (int): ID користувача.
        title (str): Назва події.
        date (date): Дата події.
        time (time): Час події.

    Returns:
        bool: True, якщо подія існує, інакше False.
    """
    stmt = select(Event).where(
        Event.user_id == user_id,
        Event.title == title,
        Event.date == date,
        Event.time == time
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def mark_event_as_done(session, event_id: int, user_id: int) -> bool:
    """
    Позначає подію як виконану, якщо вона належить вказаному користувачу.

    Args:
        session: Активна сесія SQLAlchemy.
        event_id (int): ID події.
        user_id (int): ID користувача.

    Returns:
        bool: True, якщо оновлення виконано, False — якщо подія не знайдена або не належить користувачу.
    """
    stmt = select(Event).where(Event.id == event_id)
    result = await session.execute(stmt)
    event = result.scalar_one_or_none()

    if not event or event.user_id != user_id:
        return False

    event.is_done = True
    await session.commit()
    return True


async def save_event(session, event: Event):
    """
    Зберігає зміни об'єкта події у базі даних.

    Args:
        session: Активна сесія SQLAlchemy.
        event (Event): Подія для збереження.
    """
    await session.commit()


async def delete_event(session, event: Event):
    """
    Видаляє подію з бази даних.

    Args:
        session: Активна сесія SQLAlchemy.
        event (Event): Подія для видалення.
    """
    await session.delete(event)
    await session.commit()
