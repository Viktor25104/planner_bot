from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta
from app.services.event_list_service import (
    list_events, export_one_to_google,
    export_all_to_google, import_from_google_calendar
)
from app.utils.i18n import L

router = Router()


@router.message(F.text.startswith("/list"))
async def list_nearest(message: Message):
    """
    Обробляє команду /list.

    Виводить події на сьогодні та завтра.
    """
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    await list_events(message, today, tomorrow, L({
        "uk": "📅 <b>Найближчі події:</b>",
        "en": "📅 <b>Upcoming events:</b>"
    }))


@router.message(F.text.startswith("/today"))
async def list_today(message: Message):
    """
    Обробляє команду /today.

    Виводить події тільки на сьогодні.
    """
    today = datetime.now().date()
    await list_events(message, today, today, L({
        "uk": "📅 <b>Події на сьогодні:</b>",
        "en": "📅 <b>Today's events:</b>"
    }))


@router.message(F.text.startswith("/week"))
async def list_week(message: Message):
    """
    Обробляє команду /week.

    Виводить події на найближчі 7 днів (включно з поточним днем).
    """
    start = datetime.now().date()
    end = start + timedelta(days=6)
    await list_events(message, start, end, L({
        "uk": "🗓 <b>Події на тиждень:</b>",
        "en": "🗓 <b>Events for the week:</b>"
    }))


@router.message(F.text.startswith("/month"))
async def list_month(message: Message):
    """
    Обробляє команду /month.

    Виводить події за поточний календарний місяць.
    """
    now = datetime.now()
    start = now.replace(day=1).date()
    # Знаходимо останній день місяця
    end = (now.replace(month=now.month % 12 + 1, day=1) - timedelta(days=1)).date()
    await list_events(message, start, end, L({
        "uk": "📂 <b>Події цього місяця:</b>",
        "en": "📂 <b>Events this month:</b>"
    }))


@router.callback_query(F.data.startswith("export_google:"))
async def export_google(callback: CallbackQuery):
    """
    Обробляє callback для експорту однієї події в Google Calendar.

    Отримує ID події з callback-даних.
    """
    event_id = int(callback.data.split(":")[1])
    await export_one_to_google(callback, event_id)


@router.message(F.text == "/export_all")
async def export_all(message: Message):
    """
    Обробляє команду /export_all.

    Експортує всі події користувача в Google Calendar.
    """
    await export_all_to_google(message)


@router.message(F.text == "/import_google")
async def import_google(message: Message):
    """
    Обробляє команду /import_google.

    Імпортує події користувача з Google Calendar у систему.
    """
    await import_from_google_calendar(message)
