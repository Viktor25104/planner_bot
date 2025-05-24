import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import config
from app.scheduler.scheduler import start_scheduler
from app.utils.i18n import L

from app.handlers import (
    event_start,
    event_menu,
    event_add,
    event_list,
    event_delete,
    event_edit,
    event_cancel,
    event_stats,
    event_chart,
    event_export,
    event_done,
    event_fallback,
)

routers = [
    event_start.router,
    event_menu.router,
    event_add.router,
    event_list.router,
    event_delete.router,
    event_edit.router,
    event_cancel.router,
    event_stats.router,
    event_chart.router,
    event_export.router,
    event_done.router,
    event_fallback.router,
]


async def on_startup(bot: Bot):
    for admin_id in config.bot.admin_ids:
        try:
            await bot.send_message(admin_id,
                                   L({"uk": "🤖 Бот успішно запущено!", "en": "🤖 Bot successfully started!"}))
        except Exception as e:
            pass


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    for router in routers:
        dp.include_router(router)

    await start_scheduler()
    await on_startup(bot)
    await dp.start_polling(bot, skip_updates=config.bot.skip_updates)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
