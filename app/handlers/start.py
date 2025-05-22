from aiogram import Router, F
from aiogram.types import Message
from app.db import async_session
from app.services.user_service import handle_user_start
from app.handlers.menu import build_main_menu
from app.utils.i18n import L

router = Router()


@router.message(F.text == "/start")
async def start_handler(message: Message):
    """
    Обробляє команду /start.

    Реєструє нового користувача або показує повідомлення, якщо вже зареєстрований.
    Виводить головне меню після відповіді.
    """
    async with async_session() as session:
        try:
            user, is_new = await handle_user_start(
                session,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )

            if is_new:
                await message.answer(
                    L({
                        "uk": f"👋 Привіт, {user.first_name or 'користувачу'}! Вас зареєстровано ✅",
                        "en": f"👋 Hello, {user.first_name or 'user'}! You have been registered ✅"
                    }),
                    reply_markup=build_main_menu()
                )
            else:
                await message.answer(
                    L({
                        "uk": "🔄 Ви вже зареєстровані в системі.",
                        "en": "🔄 You are already registered in the system."
                    }),
                    reply_markup=build_main_menu()
                )
        except Exception:
            # Загальний виняток
            await message.answer(
                L({
                    "uk": "⚠️ Виникла помилка при збереженні.",
                    "en": "⚠️ An error occurred while saving."
                })
            )
