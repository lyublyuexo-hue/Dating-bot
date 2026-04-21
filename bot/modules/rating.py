from typing import Optional
from sqlalchemy import select, func
from database.models import User, ActivityLog
from database.session import Session

POINTS = {
    "login":        1,
    "like":         1,
    "match":        5,
    "profile_fill": 3,
}


class RatingModule:

    @staticmethod
    async def add_points(user_id: int, action: str, points: Optional[int] = None):
        pts = points if points is not None else POINTS.get(action, 0)
        if pts == 0:
            return
        async with Session() as s:
            s.add(ActivityLog(user_id=user_id, action=action, points=pts))
            user = await s.get(User, user_id)
            if user:
                user.activity_score = (user.activity_score or 0) + pts
            await s.commit()

    @staticmethod
    async def get_score(user_id: int) -> int:
        async with Session() as s:
            result = await s.execute(
                select(func.sum(ActivityLog.points))
                .where(ActivityLog.user_id == user_id)
            )
            return result.scalar() or 0