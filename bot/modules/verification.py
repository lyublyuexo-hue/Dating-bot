from telegram import Bot
from database.models import User
from database.session import Session
from bot.i18n import t


class VerificationModule:

    @staticmethod
    async def request_verification(user_id: int, bot: Bot, lang: str = "ru"):
        await bot.send_message(user_id, t("verify_request", lang), parse_mode="HTML")
        async with Session() as s:
            user = await s.get(User, user_id)
            if user:
                user.verification_status = "pending"
                await s.commit()

    @staticmethod
    async def approve(user_id: int, bot: Bot):
        async with Session() as s:
            user = await s.get(User, user_id)
            if user:
                lang = user.lang or "ru"
                user.verification_status = "verified"
                await s.commit()
        await bot.send_message(user_id, t("verify_approved", lang))

    @staticmethod
    async def reject(user_id: int, bot: Bot):
        async with Session() as s:
            user = await s.get(User, user_id)
            if user:
                lang = user.lang or "ru"
                user.verification_status = "rejected"
                await s.commit()
        await bot.send_message(user_id, t("verify_rejected", lang))