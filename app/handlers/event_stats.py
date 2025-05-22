from aiogram import Router, F
from aiogram.types import Message
from app.db import async_session
from app.services.stats_service import get_stats_report

router = Router()

@router.message(F.text.startswith("/stats"))
async def stats_handler(message: Message):
    """
    Обробляє команду /stats [mode].

    За замовчуванням відображає всі статистичні дані.
    Може приймати аргумент, наприклад: /stats category або /stats tag.

    Параметри:
        message (Message): вхідне повідомлення від користувача.

    Відповідь:
        Надсилає згенерований текстовий звіт користувачу.
    """
    args = message.text.strip().split()
    mode = args[1] if len(args) > 1 else "all"

    async with async_session() as session:
        # Повертається кортеж (raw_data, formatted_string), беремо лише текст
        _, result = await get_stats_report(session, message.from_user.id, mode)

    await message.answer(result)
