import csv
import io
from aiogram.types import BufferedInputFile
from app.repositories.user_repo import get_user_by_telegram_id
from app.repositories.event_repo import get_events_by_user
from app.utils.i18n import L


async def generate_csv_export(session, telegram_id: int) -> BufferedInputFile | None:
    """
    Генерує CSV-файл з подіями користувача.

    Args:
        session: SQLAlchemy сесія.
        telegram_id (int): Telegram ID користувача.

    Returns:
        BufferedInputFile | None: CSV-файл або None, якщо користувача або подій немає.
    """
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return None

    lang = user.language
    events = await get_events_by_user(session, user.id, ordered=True)
    if not events:
        return None

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow([
        L({"uk": "Назва", "en": "Title"}, lang),
        L({"uk": "Дата", "en": "Date"}, lang),
        L({"uk": "Час", "en": "Time"}, lang),
        L({"uk": "Категорія", "en": "Category"}, lang),
        L({"uk": "Теги", "en": "Tags"}, lang),
        L({"uk": "Нагадування", "en": "Reminder"}, lang),
        L({"uk": "Повтор", "en": "Repeat"}, lang),
        L({"uk": "Завершено", "en": "Done"}, lang)
    ])

    for e in events:
        writer.writerow([
            e.title,
            e.date.strftime("%d.%m.%Y"),
            e.time.strftime("%H:%M") if e.time else "",
            e.category or "",
            e.tag or "",
            e.remind_before,
            e.repeat,
            L({"uk": "✅", "en": "✅"}, lang) if e.is_done else L({"uk": "❌", "en": "❌"}, lang)
        ])

    buffer.seek(0)
    byte_file = io.BytesIO(buffer.read().encode("utf-8"))
    byte_file.name = "events.csv"
    return BufferedInputFile(byte_file.read(), filename="events.csv")
