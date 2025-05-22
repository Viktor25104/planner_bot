from aiogram import Router, F
from aiogram.types import Message
from app.services.export_service import generate_csv_export
from app.db import async_session
from app.utils.i18n import L

router = Router()

@router.message(F.text == "/export_csv")
async def export_csv(message: Message):
    """
    Обробляє команду /export_csv.

    Генерує CSV-файл з подіями користувача:
    - Якщо користувач не зареєстрований — надсилає відповідне повідомлення.
    - Якщо подій немає — повідомляє про це.
    - Інакше — надсилає CSV-файл з експортованими подіями.
    """
    async with async_session() as session:
        result = await generate_csv_export(session, message.from_user.id)

        if result is None:
            # Користувач не знайдений у базі
            await message.answer(L({
                "uk": "⚠️ Ви ще не зареєстровані. Напишіть /start.",
                "en": "⚠️ You are not registered yet. Please send /start."
            }))
        elif result is False:
            # Події відсутні
            await message.answer(L({
                "uk": "📭 У вас немає подій для експорту.",
                "en": "📭 You have no events to export."
            }))
        else:
            # Надсилання файлу
            await message.answer_document(document=result)
