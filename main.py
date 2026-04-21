import logging
from telegram.ext import Application, CommandHandler
from config import settings
from database.models import init_db
from bot.modules.tags import TagModule
from bot.handlers.registration import register_handlers as reg_handlers
from bot.handlers.browsing    import register_handlers as browse_handlers
from bot.handlers.matches     import register_handlers as match_handlers
from bot.handlers.profile     import register_handlers as profile_handlers
from bot.handlers.admin       import register_handlers as admin_handlers
from bot.handlers.complaint   import register_handlers as complaint_handlers
from bot.handlers.home        import register_handlers as home_handlers
from bot.keyboards.main import language_kb
from bot.i18n import t

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(app: Application):
    await init_db()
    await TagModule.seed_tags()
    await app.bot.set_my_commands([
        ("start",     "🚀 Начать / Boshlash"),
        ("language",  "🌐 Изменить язык / Til"),
        ("complaint", "✉️ Написать админу"),
    ])
    logger.info("Bot initialized!")

async def cmd_language(update, ctx):
    await update.message.reply_text(
        "🌐 Выбери язык / Tilni tanlang:",
        reply_markup=language_kb()
    )


def main():
    app = (
        Application.builder()
        .token(settings.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    reg_handlers(app)        # /start — ConversationHandler
    complaint_handlers(app)  # /complaint
    admin_handlers(app)      # /admin
    browse_handlers(app)     # like / skip / report
    match_handlers(app)      # матчи
    profile_handlers(app)    # профиль
    home_handlers(app)       # меню + inline

    app.add_handler(CommandHandler("language", cmd_language))

    logger.info("Bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()