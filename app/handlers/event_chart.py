from aiogram import Router, F
from aiogram.types import Message
from app.services.chart_service import build_charts_for_user

router = Router()

@router.message(F.text.startswith("/chart"))
async def chart_handler(message: Message):
    """
    Обробляє команду /chart [mode].

    Якщо вказано аргумент, використовує його як режим побудови графіку.
    Інакше за замовчуванням будує графік для всіх подій.
    """
    args = message.text.strip().split()
    mode = args[1] if len(args) > 1 else "all"
    await build_charts_for_user(message, mode)
