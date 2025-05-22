import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from aiogram.types import Message, FSInputFile

from app.db import async_session
from app.repositories.user_repo import get_user_by_telegram_id
from app.repositories.event_repo import get_events_by_user
from app.utils.i18n import L


async def build_charts_for_user(message: Message, mode: str):
    """
    Будує діаграми активності, статусу та категорій подій користувача за період.

    Args:
        message (Message): Повідомлення користувача.
        mode (str): Період ('month', 'week', 'year', 'all').

    Відповідь:
        Надсилає кілька зображень-графіків або повідомлення про відсутність подій.
    """
    now = datetime.now()

    if mode == "month":
        date_from = now.replace(day=1).date()
        title = L({"uk": "за місяць", "en": "for the month"})
    elif mode == "week":
        date_from = (now - timedelta(days=now.weekday())).date()
        title = L({"uk": "за тиждень", "en": "for the week"})
    elif mode == "year":
        date_from = now.replace(month=1, day=1).date()
        title = L({"uk": "за рік", "en": "for the year"})
    else:
        date_from = None
        title = L({"uk": "за весь час", "en": "for all time"})

    async with async_session() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)

        if not user:
            await message.answer(L({
                "uk": "⚠️ Ви ще не зареєстровані. Напишіть /start.",
                "en": "⚠️ You are not registered yet. Please send /start."
            }))
            return

        events = await get_events_by_user(session, user.id)

    if not events:
        await message.answer(L({
            "uk": "ℹ️ Подій поки немає.",
            "en": "ℹ️ No events yet."
        }))
        return

    filtered = [e for e in events if not date_from or e.date >= date_from]
    if not filtered:
        await message.answer(L({
            "uk": f"ℹ️ Подій {title} немає.",
            "en": f"ℹ️ No events {title}."
        }))
        return

    user_id = message.from_user.id
    path1 = _build_activity_chart(filtered, title, user_id)
    path2 = _build_status_chart(filtered, title, user_id)
    path3 = _build_category_chart(filtered, user_id)

    await message.answer_photo(FSInputFile(path1), caption=L({
        "uk": f"📈 Загальна активність {title}",
        "en": f"📈 Overall activity {title}"
    }))
    await message.answer_photo(FSInputFile(path2), caption=L({
        "uk": f"📊 Статус подій {title}",
        "en": f"📊 Event status {title}"
    }))
    if path3:
        await message.answer_photo(FSInputFile(path3), caption=L({
            "uk": "📘 Категорії подій",
            "en": "📘 Event categories"
        }))

    os.remove(path1)
    os.remove(path2)
    if path3:
        os.remove(path3)


def _build_activity_chart(events, title, user_id):
    """
    Створює гістограму загальної активності по днях.
    """
    daily = Counter(e.date for e in events)
    days = sorted(daily.keys())
    x = [d.strftime("%d.%m") for d in days]
    y = [daily[d] for d in days]

    path = f"chart_activity_{user_id}.png"
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(x, y, color="#4fa9f2")
    ax.set_title(f"📅 " + L({"uk": f"Події {title}", "en": f"Events {title}"}))
    ax.set_xlabel(L({"uk": "Дата", "en": "Date"}))
    ax.set_ylabel(L({"uk": "Кількість", "en": "Count"}))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def _build_status_chart(events, title, user_id):
    """
    Створює комбіновану діаграму статусів подій:
    - ✅ виконано
    - ⚠️ прострочено
    - 📅 заплановано
    """
    now = datetime.now()
    status_by_day = defaultdict(lambda: {"done": 0, "expired": 0, "upcoming": 0})
    for e in events:
        key = e.date
        dt = datetime.combine(e.date, e.time or now.time())
        if e.is_done:
            status_by_day[key]["done"] += 1
        elif dt < now:
            status_by_day[key]["expired"] += 1
        else:
            status_by_day[key]["upcoming"] += 1

    days = sorted(status_by_day)
    x = [d.strftime("%d.%m") for d in days]
    done = [status_by_day[d]["done"] for d in days]
    expired = [status_by_day[d]["expired"] for d in days]
    upcoming = [status_by_day[d]["upcoming"] for d in days]

    path = f"chart_status_{user_id}.png"
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(x, done, label=L({"uk": "✅ Виконано", "en": "✅ Done"}), color="#7ed957")
    ax.bar(x, expired, bottom=done, label=L({"uk": "⚠️ Прострочено", "en": "⚠️ Expired"}), color="#f49e4c")
    ax.bar(x, upcoming, bottom=[d + e for d, e in zip(done, expired)], label=L({"uk": "📅 Майбутні", "en": "📅 Upcoming"}), color="#4fa9f2")
    ax.set_title(L({"uk": f"Статус подій {title}", "en": f"Event status {title}"}))
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def _build_category_chart(events, user_id):
    """
    Створює кругову діаграму розподілу подій за категоріями.
    """
    cat_count = Counter(e.category for e in events if e.category)
    if not cat_count:
        return None

    path = f"chart_categories_{user_id}.png"
    fig, ax = plt.subplots()
    labels = list(cat_count.keys())
    sizes = list(cat_count.values())
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.set_title(L({"uk": "Розподіл подій за категоріями", "en": "Event distribution by category"}))
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path
