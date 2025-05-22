from datetime import datetime, timedelta
from app.repositories.user_repo import get_user_by_telegram_id
from app.repositories.event_repo import get_events_by_user
from app.utils.i18n import L


async def get_stats_report(session, telegram_id: int, mode: str) -> str:
    """
    Створює текстовий статистичний звіт для користувача за вибраний період.

    Args:
        session: SQLAlchemy сесія.
        telegram_id (int): Telegram ID користувача.
        mode (str): Період: "week", "month", "year" або інше (весь час).

    Returns:
        Tuple[user, str]: Користувач та згенерований текстовий звіт або повідомлення про відсутність подій.
    """
    now = datetime.now()

    if mode == "month":
        date_from = now.replace(day=1).date()
    elif mode == "week":
        date_from = (now - timedelta(days=now.weekday())).date()
    elif mode == "year":
        date_from = now.replace(month=1, day=1).date()
    else:
        date_from = None

    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return None, L({
            "uk": "⚠️ Ви ще не зареєстровані. Напишіть /start.",
            "en": "⚠️ You are not registered yet. Please send /start."
        })

    lang = user.language
    events = await get_events_by_user(session, user.id, ordered=False)
    if not events:
        return None, L({
            "uk": "ℹ️ У вас ще немає подій.",
            "en": "ℹ️ You have no events yet."
        }, lang)

    filtered = [e for e in events if not date_from or e.date >= date_from]

    total = len(filtered)
    done = sum(e.is_done for e in filtered)
    upcoming = sum(
        not e.is_done and datetime.combine(e.date, e.time or now.time()) >= now
        for e in filtered
    )
    expired = total - done - upcoming

    categories = {}
    repeats = {}
    for e in filtered:
        if e.category:
            categories[e.category] = categories.get(e.category, 0) + 1
        if e.repeat and e.repeat != "none":
            repeats[e.repeat] = repeats.get(e.repeat, 0) + 1

    top_category = max(categories.items(), key=lambda x: x[1])[0] if categories else "-"
    top_repeats = ", ".join(f"{k}: {v}" for k, v in repeats.items()) if repeats else "—"

    report = L({
        "uk": (
            f"📊 <b>Статистика {mode}:</b>\n\n"
            f"• Загалом подій: <b>{total}</b>\n"
            f"• Виконано: ✅ <b>{done}</b>\n"
            f"• Прострочено: ⚠️ <b>{expired}</b>\n"
            f"• Майбутні: 📅 <b>{upcoming}</b>\n\n"
            f"🏷 Найчастіша категорія: <b>{top_category}</b>\n"
            f"🔁 Активні повторення: {top_repeats}"
        ),
        "en": (
            f"📊 <b>Statistics for {mode}:</b>\n\n"
            f"• Total events: <b>{total}</b>\n"
            f"• Done: ✅ <b>{done}</b>\n"
            f"• Expired: ⚠️ <b>{expired}</b>\n"
            f"• Upcoming: 📅 <b>{upcoming}</b>\n\n"
            f"🏷 Most common category: <b>{top_category}</b>\n"
            f"🔁 Active repeats: {top_repeats}"
        )
    }, lang)

    return user, report
