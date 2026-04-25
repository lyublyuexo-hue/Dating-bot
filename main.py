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

    # ✅ ПОРЯДОК КРИТИЧЕСКИ ВАЖЕН:
    # 1. ConversationHandler (/start) — первым, чтобы перехватывал фото при регистрации
    reg_handlers(app)

    # 2. Команды
    complaint_handlers(app)
    admin_handlers(app)

    # 3. Меню (Reply-кнопки + inline) — ДО profile, чтобы кнопки меню не перехватывались
    home_handlers(app)

    # 4. Просмотр анкет и матчи
    browse_handlers(app)
    match_handlers(app)

    # 5. Профиль — ПОСЛЕДНИМ, его общий filters.TEXT не должен перехватывать кнопки меню

    profile_handlers(app)

    app.add_handler(CommandHandler("language", cmd_language))

    logger.info("Bot started!")

    async def debug_all(update, ctx):
        print(f">>> ЛЮБОЕ СООБЩЕНИЕ: {update.message.text if update.message else 'no message'}")

    from telegram.ext import MessageHandler, filters as f2
    app.add_handler(MessageHandler(f2.ALL, debug_all), group=999),

    app.run_polling(drop_pending_updates=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("telegram.ext.ConversationHandler").setLevel(logging.DEBUG)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG  # ← меняй INFO на DEBUG
)

if __name__ == "__main__":
    main()