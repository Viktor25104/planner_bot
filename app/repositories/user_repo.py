from sqlalchemy import select
from app.models.models import User

async def get_user_by_telegram_id(session, telegram_id: int):
    """
    Отримує користувача за його Telegram ID.

    Args:
        session: Активна сесія SQLAlchemy.
        telegram_id (int): Унікальний Telegram ID.

    Returns:
        User | None: Користувач або None, якщо не знайдено.
    """
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_or_create_user(session, telegram_id: int, username: str, first_name: str, last_name: str):
    """
    Отримує користувача за Telegram ID або створює нового, якщо його ще немає.

    Args:
        session: Активна сесія SQLAlchemy.
        telegram_id (int): Telegram ID користувача.
        username (str): Ім'я користувача.
        first_name (str): Ім'я.
        last_name (str): Прізвище.

    Returns:
        Tuple[User, bool]: Повертає пару (користувач, чи був створений новий).
    """
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)
        await session.commit()
        return user, True
    return user, False
