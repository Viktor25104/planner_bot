from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.services.event_delete_service import show_events_for_deletion, delete_event_by_callback

router = Router()

@router.message(F.text == "/delete")
async def delete_command(message: Message):
    """
    Обробляє команду /delete.

    Відображає для користувача список подій, доступних для видалення.
    """
    await show_events_for_deletion(message)


@router.callback_query(F.data.startswith("delete_event:"))
async def confirm_delete(callback: CallbackQuery):
    """
    Обробляє callback при підтвердженні видалення події.

    Отримує ID події з callback-даних та викликає логіку видалення.
    """
    event_id = int(callback.data.split(":")[1])
    await delete_event_by_callback(callback, event_id)
