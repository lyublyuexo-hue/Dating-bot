from typing import Optional
from telegram import Bot

class NotificationService:
    @staticmethod
    async def notify_match(bot: Bot, user1_id: int, user2_id: int,
                           user1_name: str, user2_name: str,
                           user1_username: Optional[str], user2_username: Optional[str],
                           common_tags_text: str = ""):
        link1 = f"@{user1_username}" if user1_username else "в личку"
        link2 = f"@{user2_username}" if user2_username else "в личку"
        await bot.send_message(user1_id,
            f"💘 Мэтч с {user2_name}! Пиши: {link2}{common_tags_text}")
        await bot.send_message(user2_id,
            f"💘 Мэтч с {user1_name}! Пиши: {link1}{common_tags_text}")
