from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from bot.keyboards.main import language_kb
from bot.i18n import t


async def cmd_language(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌐 Выбери язык / Tilni tanlang:",
        reply_markup=language_kb()
    )


def register_handlers(app: Application):
    app.add_handler(CommandHandler("language", cmd_language))