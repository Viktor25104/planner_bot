import csv
import io
import json

from aiogram.types import BufferedInputFile
from app.repositories.user_repo import get_user_by_telegram_id
from app.repositories.event_repo import get_events_by_user
from app.utils.i18n import L
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor


async def generate_csv_export(session, telegram_id: int) -> BufferedInputFile | None:
    """
    Генерує CSV-файл з подіями користувача.
    """
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return None

    lang = user.language
    events = await get_events_by_user(session, user.id, ordered=True)
    if not events:
        return False

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
    byte_file = io.BytesIO(buffer.read().encode("utf-8-sig"))
    return BufferedInputFile(byte_file.read(), filename="events.csv")


async def generate_txt_export(session, telegram_id: int) -> BufferedInputFile | None:
    """
    Генерує текстовий файл з подіями користувача (plain text).
    """
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return None
    events = await get_events_by_user(session, user.id, ordered=True)
    if not events:
        return False

    lang = user.language
    buffer = io.StringIO()
    for e in events:
        buffer.write(f"{e.title}\n")
        buffer.write(f"{e.date.strftime('%d.%m.%Y')} {e.time.strftime('%H:%M') if e.time else ''}\n")
        if e.category:
            buffer.write(f"{L({'uk': 'Категорія', 'en': 'Category'}, lang)}: {e.category}\n")
        if e.tag:
            buffer.write(f"{L({'uk': 'Теги', 'en': 'Tags'}, lang)}: {e.tag}\n")
        buffer.write(f"{L({'uk': 'Повтор', 'en': 'Repeat'}, lang)}: {e.repeat}\n")
        buffer.write(f"{L({'uk': 'Завершено', 'en': 'Done'}, lang)}: {'✅' if e.is_done else '❌'}\n")
        buffer.write("\n")
    byte_file = io.BytesIO(buffer.getvalue().encode("utf-8"))
    return BufferedInputFile(byte_file.read(), filename="events.txt")


async def generate_json_export(session, telegram_id: int) -> BufferedInputFile | None:
    """
    Генерує JSON-файл з подіями користувача.
    """
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return None
    events = await get_events_by_user(session, user.id, ordered=True)
    if not events:
        return False

    event_list = [
        {
            "title": e.title,
            "date": e.date.isoformat(),
            "time": e.time.strftime("%H:%M") if e.time else None,
            "category": e.category,
            "tag": e.tag,
            "remind_before": e.remind_before,
            "repeat": e.repeat,
            "done": e.is_done
        } for e in events
    ]
    buffer = io.StringIO(json.dumps(event_list, ensure_ascii=False, indent=2))
    byte_file = io.BytesIO(buffer.getvalue().encode("utf-8"))
    return BufferedInputFile(byte_file.read(), filename="events.json")


async def generate_excel_export(session, telegram_id: int) -> BufferedInputFile | None:
    """
    Генерує Excel-файл (XLSX) з подіями користувача.
    """
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return None
    events = await get_events_by_user(session, user.id, ordered=True)
    if not events:
        return False

    lang = user.language
    wb = Workbook()
    ws = wb.active
    ws.title = "Events"

    headers = [
        L({"uk": "Назва", "en": "Title"}, lang),
        L({"uk": "Дата", "en": "Date"}, lang),
        L({"uk": "Час", "en": "Time"}, lang),
        L({"uk": "Категорія", "en": "Category"}, lang),
        L({"uk": "Теги", "en": "Tags"}, lang),
        L({"uk": "Нагадування", "en": "Reminder"}, lang),
        L({"uk": "Повтор", "en": "Repeat"}, lang),
        L({"uk": "Завершено", "en": "Done"}, lang)
    ]
    ws.append(headers)

    for e in events:
        ws.append([
            e.title,
            e.date.strftime("%d.%m.%Y"),
            e.time.strftime("%H:%M") if e.time else "",
            e.category or "",
            e.tag or "",
            e.remind_before,
            e.repeat,
            "✅" if e.is_done else "❌"
        ])

    file_stream = io.BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    return BufferedInputFile(file_stream.read(), filename="events.xlsx")


async def generate_pdf_export(session, telegram_id: int) -> BufferedInputFile | None:
    """
    Генерує PDF-файл з подіями користувача (список).
    """
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return None
    events = await get_events_by_user(session, user.id, ordered=True)
    if not events:
        return False

    lang = user.language
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    pdfmetrics.registerFont(TTFont("DejaVu", "static/fonts/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", "static/fonts/DejaVuSans-Bold.ttf"))

    c.setFont("DejaVu-Bold", 18)
    c.drawCentredString(width / 2, y, L({"uk": "Події користувача", "en": "User Events"}, lang))
    y -= 30
    c.setFont("DejaVu", 11)

    for e in events:
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("DejaVu", 11)

        c.setFillColor(HexColor("#f5f5f5"))
        c.roundRect(30, y - 80, width - 60, 75, 5, fill=1, stroke=0)
        c.setFillColor(HexColor("#000000"))

        block_y = y - 15
        c.setFont("DejaVu-Bold", 12)
        c.drawString(40, block_y, f"{e.title}")
        block_y -= 14

        c.setFont("DejaVu", 11)
        c.drawString(50, block_y, f"{e.date.strftime('%d.%m.%Y')} {e.time.strftime('%H:%M') if e.time else ''}")
        block_y -= 13

        if e.category:
            c.drawString(50, block_y, f"{L({'uk': 'Категорія', 'en': 'Category'}, lang)}: {e.category}")
            block_y -= 13
        if e.tag:
            c.drawString(50, block_y, f"{L({'uk': 'Теги', 'en': 'Tags'}, lang)}: {e.tag}")
            block_y -= 13

        c.drawString(50, block_y, f"{L({'uk': 'Повтор', 'en': 'Repeat'}, lang)}: {e.repeat}")
        block_y -= 13
        c.drawString(50, block_y, f"{L({'uk': 'Готово', 'en': 'Done'}, lang)}: {'Так' if e.is_done else 'Ні'}")

        y -= 100

    c.save()
    buffer.seek(0)
    return BufferedInputFile(buffer.read(), filename="events.pdf")
