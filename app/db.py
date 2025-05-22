from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import config

# Ініціалізація асинхронного движка SQLAlchemy
engine = create_async_engine(
    config.db.db_url,
    echo=False,
    future=True
)

# Асинхронна сесія збереження
async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)


class Base(DeclarativeBase):
    """
    Базовий клас для всіх моделей ORM.
    """
    pass


async def get_session() -> AsyncSession:
    """
    Генератор асинхронної сесії бази даних для залежностей.

    Returns:
        AsyncSession: асинхронна сесія SQLAlchemy.
    """
    async with async_session() as session:
        yield session
