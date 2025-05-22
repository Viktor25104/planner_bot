from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.handlers.menu import build_main_menu
from app.utils.i18n import L

router = Router()

@router.message(F.text == "/cancel")
async def cancel_handler(message: Message, state: FSMContext):
    """
    Обробник команди /cancel для скасування поточної FSM-операції.

    Якщо немає активного стану — повідомляє користувача.
    Інакше очищає стан і повертає користувача до головного меню.
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(L({
            "uk": "❕ Немає активної операції.",
            "en": "❕ No active operation."
        }))
    else:
        await state.clear()
        await message.answer(L({
            "uk": "❌ Операцію скасовано.",
            "en": "❌ Operation cancelled."
        }), reply_markup=build_main_menu())
