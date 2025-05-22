from googleapiclient.discovery import build
from datetime import datetime, timezone
from app.integrations.google_auth import get_credentials
from app.models.models import Event
from app.db import async_session
from sqlalchemy import select
from app.utils.i18n import L
import pytz

async def export_event(user_id: int, title: str, date, time, description=""):
    """
    Експортує одну подію до Google Calendar для вказаного користувача.

    Args:
        user_id (int): Telegram ID користувача.
        title (str): Назва події.
        date (date): Дата події.
        time (time): Час події.
        description (str, optional): Опис події.

    Returns:
        str: Посилання на створену подію в Google Calendar.
    """
    creds = get_credentials(user_id)
    service = build("calendar", "v3", credentials=creds)

    start = datetime.combine(date, time).isoformat()
    end = datetime.combine(date, time).isoformat()

    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start, "timeZone": "Europe/Kyiv"},
        "end": {"dateTime": end, "timeZone": "Europe/Kyiv"},
    }

    created = service.events().insert(calendarId="primary", body=event).execute()
    return created.get("htmlLink")


async def import_events_from_google(user):
    """
    Імпортує найближчі події з Google Calendar користувача в локальну базу.

    Перевіряє події на унікальність (за user_id, title і date),
    додає лише нові події.

    Args:
        user: Об'єкт користувача з атрибутами .id та .telegram_id

    Returns:
        int: Кількість імпортованих подій.
    """
    creds = get_credentials(user.telegram_id)
    service = build("calendar", "v3", credentials=creds)

    now = datetime.utcnow().isoformat() + "Z"  # Поточний час у форматі RFC3339
    events_result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=50,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    items = events_result.get("items", [])
    imported_count = 0

    async with async_session() as session:
        for item in items:
            title = item.get("summary", item.get("title", ""))
            description = item.get("description", "")
            start = item["start"].get("dateTime") or item["start"].get("date")
            date_obj = datetime.fromisoformat(start).astimezone(pytz.timezone("Europe/Kyiv"))

            # Перевірка на наявність події в базі
            stmt = select(Event).where(
                Event.user_id == user.id,
                Event.title == title,
                Event.date == date_obj.date()
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                continue  # Подія вже існує

            new_event = Event(
                user_id=user.id,
                title=title,
                date=date_obj.date(),
                time=date_obj.time(),
                description=description,
                category="Імпорт",
                tag="google"
            )
            session.add(new_event)
            imported_count += 1

        await session.commit()

    return imported_count
