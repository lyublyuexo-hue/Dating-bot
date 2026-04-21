from sqlalchemy import select
from database.models import User, Tag
from database.session import Session


class MutualInterestsModule:

    @staticmethod
    async def get_common_tags(user1_id: int, user2_id: int) -> list[Tag]:
        async with Session() as s:
            u1 = await s.get(User, user1_id)
            u2 = await s.get(User, user2_id)
            if not u1 or not u2:
                return []
            ids1 = {tag.id for tag in u1.tags}
            ids2 = {tag.id for tag in u2.tags}
            common_ids = ids1 & ids2
            if not common_ids:
                return []
            result = await s.execute(
                select(Tag).where(Tag.id.in_(common_ids))
            )
            return result.scalars().all()

    @staticmethod
    def format_common_tags(tags: list[Tag]) -> str:
        if not tags:
            return ""
        items = " ".join(f"{t.emoji}{t.name}" for t in tags)
        return f"\n\n🎯 Общие интересы: {items}"