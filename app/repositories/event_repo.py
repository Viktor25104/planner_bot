from sqlalchemy import select, and_
from datetime import date, timedelta
from app.models.models import Event

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


async def delete_event(session, event: Event):
    """
    Видаляє подію з бази.

    Args:
        session: Активна сесія SQLAlchemy.
        event (Event): Подія для видалення.
    """
    await session.delete(event)
    await session.commit()


async def save_event(session, event: Event):
    """
    Зберігає зміни події у базі.

    Args:
        session: Активна сесія SQLAlchemy.
        event (Event): Подія для збереження.
    """
    await session.commit()


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
