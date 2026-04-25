from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from database.models import (
    User, Tag, Like, ProfileView, Report, ActivityLog,
    Favorite, Referral, BlackList, Premium, VipPremium
)
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
        """
        Удаляет пользователя и все связанные записи.
        SQLite не делает каскадное удаление автоматически —
        удаляем связанные таблицы вручную.
        """
        async with Session() as s:
            user = await s.get(User, telegram_id)
            if not user:
                return False

            uid = telegram_id

            # Удаляем все связанные записи вручную
            await s.execute(delete(Like).where(
                (Like.from_user_id == uid) | (Like.to_user_id == uid)
            ))
            await s.execute(delete(ProfileView).where(
                (ProfileView.viewer_id == uid) | (ProfileView.target_id == uid)
            ))
            await s.execute(delete(Report).where(
                (Report.reporter_id == uid) | (Report.target_id == uid)
            ))
            await s.execute(delete(ActivityLog).where(
                ActivityLog.user_id == uid
            ))
            await s.execute(delete(Favorite).where(
                (Favorite.user_id == uid) | (Favorite.target_id == uid)
            ))
            await s.execute(delete(Referral).where(
                (Referral.inviter_id == uid) | (Referral.invitee_id == uid)
            ))
            await s.execute(delete(BlackList).where(
                (BlackList.user_id == uid) | (BlackList.target_id == uid)
            ))
            await s.execute(delete(Premium).where(
                Premium.user_id == uid
            ))
            await s.execute(delete(VipPremium).where(
                VipPremium.user_id == uid
            ))

            # Удаляем теги (many-to-many) и самого пользователя через raw SQL
            # чтобы избежать lazy load MissingGreenlet
            from sqlalchemy import text as sa_text
            await s.execute(sa_text("DELETE FROM user_tags WHERE user_id = :uid"), {"uid": uid})
            await s.execute(sa_text("DELETE FROM users WHERE telegram_id = :uid"), {"uid": uid})

            await s.commit()
            return True

    @staticmethod
    async def deactivate_user(telegram_id: int):
        await UserService.update_user(telegram_id, is_active=False)