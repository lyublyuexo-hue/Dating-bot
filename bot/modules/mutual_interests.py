from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models import User
from database.session import Session


class MutualInterestsModule:

    @staticmethod
    async def get_common_tags(user1_id: int, user2_id: int) -> list:
        """
        Возвращает общие теги двух пользователей.
        Загружаем теги внутри сессии через selectinload —
        иначе lazy load вне сессии вызывает MissingGreenlet.
        """
        async with Session() as s:
            result1 = await s.execute(
                select(User).options(selectinload(User.tags))
                .where(User.telegram_id == user1_id)
            )
            result2 = await s.execute(
                select(User).options(selectinload(User.tags))
                .where(User.telegram_id == user2_id)
            )
            u1 = result1.scalar_one_or_none()
            u2 = result2.scalar_one_or_none()

            if not u1 or not u2:
                return []

            ids1 = {tag.id for tag in u1.tags}
            ids2 = {tag.id for tag in u2.tags}
            common_ids = ids1 & ids2

            # Возвращаем объекты тегов из u1
            return [tag for tag in u1.tags if tag.id in common_ids]