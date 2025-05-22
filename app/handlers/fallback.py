from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.utils.i18n import L

router = Router()

@router.message()
async def unknown_input(message: Message, state: FSMContext):
    """
    Обробляє будь-яке нерозпізнане повідомлення.

    Якщо користувач знаходиться у стані FSM — повідомляє про неправильне введення.
    Якщо стану немає — пропонує використати відомі команди.
    """
    current_state = await state.get_state()
    if current_state:
        await message.answer(L({
            "uk": "⚠️ Введення не розпізнано. Спробуйте ще раз або завершіть дію.",
            "en": "⚠️ Input not recognized. Please try again or cancel the action."
        }))
    else:
        await message.answer(L({
            "uk": "🤖 Команда не розпізнана. Напишіть /start або /add.",
            "en": "🤖 Command not recognized. Please type /start or /add."
        }))
