from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models import User, Tag
from database.session import Session


class UserService:

    @staticmethod
    async def get_user(telegram_id: int) -> Optional[User]:
        async with Session() as s:
            result = await s.execute(
                select(User)
                .options(selectinload(User.tags))
                .where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_lang(telegram_id: int) -> str:
        user = await UserService.get_user(telegram_id)
        return user.lang if user else "ru"

    @staticmethod
    async def create_user(
        telegram_id: int,
        username: Optional[str],
        name: str,
        gender: str,
        age: int,
        city: str,
        photo_file_id: str,
        about: Optional[str],
        looking_for: str,
        tag_ids: List[int],
        lang: str = "ru",
    ) -> User:
        async with Session() as s:
            tags = []
            if tag_ids:
                result = await s.execute(select(Tag).where(Tag.id.in_(tag_ids)))
                tags = result.scalars().all()
            user = User(
                telegram_id=telegram_id,
                username=username,
                name=name,
                gender=gender,
                age=age,
                city=city,
                photo_file_id=photo_file_id,
                about=about,
                looking_for=looking_for,
                lang=lang,
                tags=tags,
            )
            s.add(user)
            await s.commit()
            # Возвращаем с загруженными тегами
            result = await s.execute(
                select(User)
                .options(selectinload(User.tags))
                .where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def update_user(telegram_id: int, **kwargs) -> Optional[User]:
        async with Session() as s:
            result = await s.execute(
                select(User)
                .options(selectinload(User.tags))
                .where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            for k, v in kwargs.items():
                setattr(user, k, v)
            await s.commit()
            return user

    @staticmethod
    async def delete_user(telegram_id: int) -> bool:
        async with Session() as s:
            user = await s.get(User, telegram_id)
            if not user:
                return False
            await s.delete(user)
            await s.commit()
            return True

    @staticmethod
    async def deactivate_user(telegram_id: int):
        await UserService.update_user(telegram_id, is_active=False)