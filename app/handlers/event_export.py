from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.db import async_session
from app.services.export_service import (
    generate_csv_export,
    generate_txt_export,
    generate_json_export,
    generate_pdf_export,
    generate_excel_export
)
from app.utils.i18n import L

router = Router()


@router.callback_query(F.data.startswith("export:"))
async def handle_export_callback(callback: CallbackQuery):
    format_type = callback.data.split(":")[1]

    export_map = {
        "csv": generate_csv_export,
        "txt": generate_txt_export,
        "json": generate_json_export,
        "pdf": generate_pdf_export,
        "excel": generate_excel_export
    }

    if format_type not in export_map:
        await callback.answer("❌ Unknown format")
        return

    async with async_session() as session:
        result = await export_map[format_type](session, callback.from_user.id)

        if result is None:
            await callback.message.answer("⚠️ Ви ще не зареєстровані. Напишіть /start.")
        elif result is False:
            await callback.message.answer("📭 Немає подій для експорту.")
        else:
            await callback.message.answer_document(document=result)

    await callback.answer()


@router.message(F.text == "/export_csv")
async def export_csv(message: Message):
    """
    Обробляє команду /export_csv — експортує події користувача у форматі CSV.
    """
    async with async_session() as session:
        result = await generate_csv_export(session, message.from_user.id)

        if result is None:
            await message.answer(L({"uk": "⚠️ Ви ще не зареєстровані. Напишіть /start.", "en": "⚠️ You are not registered yet. Please send /start."}))
        elif result is False:
            await message.answer(L({"uk": "📭 У вас немає подій для експорту.", "en": "📭 You have no events to export."}))
        else:
            await message.answer_document(document=result)


@router.message(F.text == "/export_txt")
async def export_txt(message: Message):
    """
    Обробляє команду /export_txt — експортує події користувача у форматі TXT.
    """
    async with async_session() as session:
        result = await generate_txt_export(session, message.from_user.id)

        if result is None:
            await message.answer(L({"uk": "⚠️ Ви ще не зареєстровані. Напишіть /start.", "en": "⚠️ You are not registered yet. Please send /start."}))
        elif result is False:
            await message.answer(L({"uk": "📭 У вас немає подій для експорту.", "en": "📭 You have no events to export."}))
        else:
            await message.answer_document(document=result)


@router.message(F.text == "/export_json")
async def export_json(message: Message):
    """
    Обробляє команду /export_json — експортує події користувача у форматі JSON.
    """
    async with async_session() as session:
        result = await generate_json_export(session, message.from_user.id)

        if result is None:
            await message.answer(L({"uk": "⚠️ Ви ще не зареєстровані. Напишіть /start.", "en": "⚠️ You are not registered yet. Please send /start."}))
        elif result is False:
            await message.answer(L({"uk": "📭 У вас немає подій для експорту.", "en": "📭 You have no events to export."}))
        else:
            await message.answer_document(document=result)


@router.message(F.text == "/export_pdf")
async def export_pdf(message: Message):
    """
    Обробляє команду /export_pdf — експортує події користувача у форматі PDF.
    """
    async with async_session() as session:
        result = await generate_pdf_export(session, message.from_user.id)

        if result is None:
            await message.answer(L({"uk": "⚠️ Ви ще не зареєстровані. Напишіть /start.", "en": "⚠️ You are not registered yet. Please send /start."}))
        elif result is False:
            await message.answer(L({"uk": "📭 У вас немає подій для експорту.", "en": "📭 You have no events to export."}))
        else:
            await message.answer_document(document=result)


@router.message(F.text == "/export_excel")
async def export_excel(message: Message):
    """
    Обробляє команду /export_excel — експортує події користувача у форматі Excel (XLSX).
    """
    async with async_session() as session:
        result = await generate_excel_export(session, message.from_user.id)

        if result is None:
            await message.answer(L({"uk": "⚠️ Ви ще не зареєстровані. Напишіть /start.", "en": "⚠️ You are not registered yet. Please send /start."}))
        elif result is False:
            await message.answer(L({"uk": "📭 У вас немає подій для експорту.", "en": "📭 You have no events to export."}))
        else:
            await message.answer_document(document=result)