from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.repositories.user_repo import get_user_by_telegram_id
from app.repositories.event_repo import get_event_by_id, get_events_in_range, get_events_by_user
from app.integrations.google_calendar import export_event, import_events_from_google
from app.utils.i18n import L
from app.db import async_session


def format_event(event) -> str:
    """
        Форматує подію у вигляді повідомлення з деталями (дата, час, категорія, теги).
    """
    date = event.date.strftime("%d.%m.%Y")
    time = event.time.strftime("%H:%M") if event.time else L({"uk": "без часу", "en": "no time"})
    lines = [f"<b>{event.title}</b>", f"📅 {date} о {time}"]
    if event.category:
        lines.append(f"📂 {L({'uk': 'Категорія', 'en': 'Category'})}: {event.category}")
    if event.tag:
        lines.append(f"🔖 {L({'uk': 'Теги', 'en': 'Tags'})}: {event.tag}")
    return "\n".join(lines)


async def list_events(message: Message, start, end, title: str, parse_args: bool = True):
    """
    Виводить список подій за вказаний період (і фільтром за категорією або тегом).
    """
    category = tag = None

    if parse_args:
        args = message.text.strip().split(maxsplit=1)
        filter_text = args[1].strip() if len(args) > 1 else None

        if filter_text:
            if filter_text.startswith("#"):
                tag = filter_text[1:]
            else:
                category = filter_text

    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(L({
                "uk": "⚠️ Ви ще не зареєстровані. Напишіть /start.",
                "en": "⚠️ You are not registered yet. Please send /start."
            }))
            return

        events = await get_events_in_range(session, user.id, start, end, category, tag)
        if not events:
            await message.answer(L({
                "uk": "📭 Подій не знайдено.",
                "en": "📭 No events found."
            }, user.language))
            return

        await message.answer(title)
        for event in events:
            await message.answer(format_event(event))


async def export_one_to_google(message: Message, event_id: int):
    """
        Експортує одну подію в Google Calendar по callback-запиту.
    """
    async with async_session() as session:
        event = await get_event_by_id(session, event_id)
        if not event:
            await message.answer(L({
                "uk": "⚠️ Подія не знайдена.",
                "en": "⚠️ Event not found."
            }))
            return

        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(L({
                "uk": "⚠️ Користувача не знайдено.",
                "en": "⚠️ User not found."
            }))
            return

        try:
            link = await export_event(
                user_id=user.telegram_id,
                title=event.title,
                date=event.date,
                time=event.time,
                description=event.description or ""
            )
            await message.answer(
                L({
                    "uk": "☁️ Подію також додано до Google Calendar!",
                    "en": "☁️ Event also exported to Google Calendar!"
                }),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Google", url=link)]])
            )
        except Exception as e:
            print(f"[Export Error] {e}")
            await message.answer(L({
                "uk": "⚠️ Помилка при експорті!",
                "en": "⚠️ Export failed!"
            }))

async def import_from_google_calendar(message: Message):
    """
        Імпортує події з Google Calendar для користувача.
    """
    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer(L({
                "uk": "⚠️ Спочатку зареєструйтесь через /start.",
                "en": "⚠️ Please register first via /start."
            }))
            return

        try:
            count = await import_events_from_google(user)
            await message.answer(L({
                "uk": f"✅ Імпортовано {count} подій з Google Календаря.",
                "en": f"✅ Imported {count} events from Google Calendar."
            }, user.language))
        except Exception as e:
            print(f"[Import Error] {e}")
            await message.answer(L({
                "uk": "❌ Помилка при імпорті з Google.",
                "en": "❌ Failed to import from Google."
            }, user.language))
