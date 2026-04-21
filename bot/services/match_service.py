from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, and_, or_, case
from sqlalchemy.orm import selectinload  # ← перенесли сюда
from database.models import User, Like
from database.session import Session


class MatchService:

    @staticmethod
    async def get_next_profile(user_id: int) -> Optional[User]:
        async with Session() as s:
            me = await s.get(User, user_id, options=[selectinload(User.tags)])
            if not me:
                return None

            seen_result = await s.execute(
                select(Like.to_user_id).where(Like.from_user_id == user_id)
            )
            seen_ids = [row[0] for row in seen_result.fetchall()]

            conditions = [
                User.telegram_id != user_id,
                User.is_active   == True,
                User.ban_status  == "active",
                User.photo_file_id.isnot(None),
                User.age >= me.age_min,
                User.age <= me.age_max,
            ]
            if seen_ids:
                conditions.append(User.telegram_id.notin_(seen_ids))
            if me.looking_for != "all":
                conditions.append(User.gender == me.looking_for)

            now            = datetime.now()
            boost_priority = case((User.boost_until > now, 1), else_=0)

            q = (
                select(User)
                .options(selectinload(User.tags))
                .where(and_(*conditions))
                .order_by(boost_priority.desc(), User.activity_score.desc())
                .limit(1)
            )
            result = await s.execute(q)
            return result.scalar_one_or_none()

    @staticmethod
    async def add_like(from_id: int, to_id: int) -> bool:
        async with Session() as s:
            like = Like(from_user_id=from_id, to_user_id=to_id)
            s.add(like)

            reverse = await s.execute(
                select(Like).where(
                    and_(Like.from_user_id == to_id, Like.to_user_id == from_id)
                )
            )
            reverse_like = reverse.scalar_one_or_none()

            if reverse_like:
                like.is_match         = True
                reverse_like.is_match = True
                await s.commit()
                return True

            await s.commit()
            return False

    @staticmethod
    async def get_matches(user_id: int) -> List[Like]:
        async with Session() as s:
            result = await s.execute(
                select(Like).where(
                    and_(
                        Like.is_match == True,
                        or_(Like.from_user_id == user_id, Like.to_user_id == user_id)
                    )
                )
            )
            return result.scalars().all()