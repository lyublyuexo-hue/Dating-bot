from sqlalchemy import select
from database.models import User, Report
from database.session import Session


class ModerationService:

    @staticmethod
    async def ban_user(user_id: int, reason: str, shadow: bool = False):
        async with Session() as s:
            user = await s.get(User, user_id)
            if user:
                user.ban_status = "shadow" if shadow else "banned"
                user.ban_reason = reason
                user.is_active  = False
                await s.commit()

    @staticmethod
    async def unban_user(user_id: int):
        async with Session() as s:
            user = await s.get(User, user_id)
            if user:
                user.ban_status = "active"
                user.ban_reason = None
                user.is_active  = True
                await s.commit()

    @staticmethod
    async def get_pending_reports():
        async with Session() as s:
            result = await s.execute(
                select(Report).where(Report.resolved == False)
                .order_by(Report.created_at.desc())
            )
            return result.scalars().all()

    @staticmethod
    async def resolve_report(report_id: int):
        async with Session() as s:
            report = await s.get(Report, report_id)
            if report:
                report.resolved = True
                await s.commit()