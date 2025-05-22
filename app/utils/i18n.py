from aiogram.types import Message
from app.db import async_session
from app.models.models import User

DEFAULT_LANG = "uk"

LANGS = {
    "uk": "🇬🇧 English",
    "en": "🇺🇦 Українська"
}

def get_switch_lang(current_lang: str) -> str:
    return "en" if current_lang == "uk" else "uk"

def get_lang_button(current_lang: str) -> str:
    return LANGS.get(current_lang, "🇬🇧 English")

async def get_current_lang(message: Message) -> str:
    from_user = message.from_user
    if not from_user:
        return DEFAULT_LANG

    async with async_session() as session:
        user = await session.get(User, from_user.id)
        if user and user.language in LANGS:
            return user.language

    return DEFAULT_LANG

def L(texts: dict, lang: str = DEFAULT_LANG) -> str:
    return texts.get(lang) or texts.get(DEFAULT_LANG) or next(iter(texts.values()))
