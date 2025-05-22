from datetime import datetime, time as dt_time, date
from typing import Optional

from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Boolean, Date, Time, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    """
    Модель користувача Telegram.

    Атрибути:
        id (int): Унікальний внутрішній ID користувача.
        telegram_id (int): Унікальний Telegram ID.
        username (str | None): Ім'я користувача Telegram.
        first_name (str | None): Ім'я користувача.
        last_name (str | None): Прізвище користувача.
        language (str): Обрана мова ('uk' або 'en').
        created_at (datetime): Дата реєстрації.
        events (list[Event]): Список подій користувача.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    language: Mapped[str] = mapped_column(default="uk")

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    events: Mapped[list["Event"]] = relationship(back_populates="user", cascade="all, delete")


class Event(Base):
    """
    Модель події користувача.

    Атрибути:
        id (int): Унікальний ID події.
        user_id (int): Зовнішній ключ до таблиці users.
        title (str): Назва події.
        description (str | None): Опис події.
        date (date): Дата події.
        time (time | None): Час події (може бути відсутній).
        created_at (datetime): Дата створення події.
        category (str | None): Категорія події.
        tag (str | None): Теги події.
        is_done (bool): Статус виконання.
        remind_before (int): За скільки хвилин надсилати нагадування.
        repeat (str | None): Тип повторення ('none', 'daily', 'weekly', 'monthly', 'yearly').
        notified (bool): Чи було вже надіслано нагадування.
        user (User): Об'єкт користувача (власник події).
    """
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    date: Mapped[date]
    time: Mapped[Optional[dt_time]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tag: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    is_done: Mapped[bool] = mapped_column(default=False)
    remind_before: Mapped[int] = mapped_column(default=10)

    repeat: Mapped[Optional[str]] = mapped_column(
        Enum("none", "daily", "weekly", "monthly", "yearly", name="repeat_enum"),
        default="none"
    )

    notified: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User"] = relationship(back_populates="events")
