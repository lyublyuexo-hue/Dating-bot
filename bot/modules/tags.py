from sqlalchemy import select
from database.models import Tag
from database.session import Session

DEFAULT_TAGS = [
    {"name": "Геймер",     "emoji": "🎮", "category": "Хобби"},
    {"name": "Аниме",      "emoji": "🎌", "category": "Хобби"},
    {"name": "Спорт",      "emoji": "⚽", "category": "Хобби"},
    {"name": "Музыка",     "emoji": "🎵", "category": "Хобби"},
    {"name": "Кино",       "emoji": "🎬", "category": "Хобби"},
    {"name": "Книги",      "emoji": "📚", "category": "Хобби"},
    {"name": "Путешествия","emoji": "✈️", "category": "Хобби"},
    {"name": "Фото",       "emoji": "📸", "category": "Хобби"},
    {"name": "Рэп",        "emoji": "🎤", "category": "Музыка"},
    {"name": "Рок",        "emoji": "🤘", "category": "Музыка"},
    {"name": "Электронная","emoji": "🎧", "category": "Музыка"},
    {"name": "Художник",   "emoji": "🎨", "category": "Творчество"},
    {"name": "Программист","emoji": "💻", "category": "Технологии"},
    {"name": "Косплей",    "emoji": "🦸", "category": "Хобби"},
]


class TagModule:

    @staticmethod
    async def seed_tags():
        async with Session() as s:
            for tag_data in DEFAULT_TAGS:
                existing = await s.execute(
                    select(Tag).where(Tag.name == tag_data["name"])
                )
                if not existing.scalar_one_or_none():
                    s.add(Tag(**tag_data))
            await s.commit()

    @staticmethod
    async def get_all_tags() -> list[Tag]:
        async with Session() as s:
            result = await s.execute(
                select(Tag).order_by(Tag.category, Tag.name)
            )
            return result.scalars().all()

    @staticmethod
    async def get_tags_by_ids(ids: list[int]) -> list[Tag]:
        async with Session() as s:
            result = await s.execute(
                select(Tag).where(Tag.id.in_(ids))
            )
            return result.scalars().all()