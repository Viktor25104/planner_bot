import asyncio
import logging
from app.scheduler.tasks import process_reminders

async def scheduler_loop():
    """
    Нескінченний цикл, який регулярно викликає обробку нагадувань.

    Запускає `process_reminders()` кожні 10 секунд.
    У разі помилки логгує її, але продовжує роботу.
    """
    while True:
        try:
            await process_reminders()
        except Exception as e:
            logging.error(f"[Scheduler] Error: {e}")
        await asyncio.sleep(10)


async def start_scheduler():
    """
    Запускає фонову задачу `scheduler_loop()` у вигляді окремої async-task.
    """
    asyncio.create_task(scheduler_loop())
