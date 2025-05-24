from googleapiclient.discovery import build
from datetime import datetime
from app.integrations.google_auth import get_credentials
from app.models.models import Event
from app.db import async_session
import pytz

from app.repositories.event_repo import exists_event


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
            if item.get("status") == "cancelled" or "birthday" in item.get("summary", "").lower():
                continue

            title = item.get("summary", item.get("title", ""))
            description = item.get("description", "")
            start = item["start"].get("dateTime") or item["start"].get("date")
            date_obj = datetime.fromisoformat(start).astimezone(pytz.timezone("Europe/Kyiv"))

            if await exists_event(session, user.id, title, date_obj.date(), date_obj.time()):
                continue

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
