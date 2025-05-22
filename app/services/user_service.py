from sqlalchemy.exc import SQLAlchemyError
from app.repositories.user_repo import get_or_create_user

async def handle_user_start(session, telegram_id, username, first_name, last_name):
    """
    Обробляє логіку старту користувача (/start):
    - Отримує або створює користувача в базі.

    Args:
        session: SQLAlchemy сесія.
        telegram_id (int): Telegram ID користувача.
        username (str): Username.
        first_name (str): Ім'я.
        last_name (str): Прізвище.

    Returns:
        Tuple[User, bool]: Користувач та булеве значення, чи був створений новий запис.
    """
    try:
        user, is_new = await get_or_create_user(session, telegram_id, username, first_name, last_name)
        return user, is_new
    except SQLAlchemyError as e:
        raise e
