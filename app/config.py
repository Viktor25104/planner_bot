from dataclasses import dataclass

@dataclass
class BotConfig:
    """
    Налаштування бота.

    Атрибути:
        token (str): Токен Telegram-бота.
        admin_ids (list[int]): Список ID адміністраторів.
        use_webhook (bool): Чи використовувати webhook.
        skip_updates (bool): Пропускати старі оновлення.
        parse_mode (str): Режим парсингу повідомлень (HTML / Markdown).
    """
    token: str
    admin_ids: list[int]
    use_webhook: bool = False
    skip_updates: bool = True
    parse_mode: str = "HTML"


@dataclass
class DBConfig:
    """
    Налаштування бази даних.

    Атрибути:
        use_postgres (bool): Використовувати PostgreSQL (True) або SQLite (False).
        db_url (str): Повний URL доступу до БД.
    """
    use_postgres: bool
    db_url: str


@dataclass
class SchedulerConfig:
    """
    Налаштування планувальника нагадувань.

    Атрибути:
        timezone (str): Часовий пояс.
        notification_times (list[int]): Список хвилин до події для нагадування.
    """
    timezone: str
    notification_times: list[int]


@dataclass
class Config:
    """
    Глобальна конфігурація додатка.
    """
    bot: BotConfig
    db: DBConfig
    scheduler: SchedulerConfig


# Поточна активна конфігурація
config = Config(
    bot=BotConfig(
        token="7606945895:AAFXrH8qOI1mdYMGgERn8yLqL-zOYDdL22Q",
        admin_ids=[],
    ),
    db=DBConfig(
        use_postgres=True,
        db_url="postgresql+asyncpg://test:password@localhost:5432/planner_db",
    ),
    scheduler=SchedulerConfig(
        timezone="Europe/Kyiv",
        notification_times=[10, 60, 1440]
    )
)
