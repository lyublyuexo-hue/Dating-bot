from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, MessageHandler, CallbackQueryHandler,
    ConversationHandler, CommandHandler, filters, ContextTypes
)
from bot.services.user_service import UserService
from bot.i18n import t
from config import settings
import time

WAITING_COMPLAINT = 1

MENU_BUTTONS = {
    "👀 Смотреть анкеты", "👀 Anketalarni ko'rish",
    "🔍 Поиск",           "🔍 Qidiruv",
    "⭐ Избранные",        "⭐ Sevimlilar",
    "🔗 Реферал",         "🔗 Referal",
    "👤 Мой профиль",     "👤 Mening anketam",
}


async def cmd_complaint(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = await UserService.get_user(update.effective_user.id)
    lang = user.lang if user else "ru"
    await update.message.reply_text(
        t("complaint_start", lang),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(t("cancel", lang), callback_data="complaint_cancel")
        ]])
    )
    return WAITING_COMPLAINT


async def handle_complaint_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("Отменено.")
    return ConversationHandler.END


async def receive_complaint(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = await UserService.get_user(update.effective_user.id)
    lang = user.lang if user else "ru"

    if update.message.text and update.message.text in MENU_BUTTONS:
        return ConversationHandler.END

    # Rate limit — раз в 30 секунд
    now  = time.time()
    last = ctx.user_data.get("last_complaint", 0)
    if now - last < 30:
        return WAITING_COMPLAINT
    ctx.user_data["last_complaint"] = now

    name     = user.name if user else update.effective_user.first_name
    username = f"@{update.effective_user.username}" if update.effective_user.username else "нет"
    uid      = update.effective_user.id

    header = (
        f"🛡 <b>Новое обращение</b>\n\n"
        f"👤 {name} ({username})\n"
        f"🆔 <code>{uid}</code>"
    )

    # Отправляем напрямую каждому админу
    for admin_id in settings.ADMIN_IDS:
        try:
            if update.message.photo:
                caption = f"{header}\n\n📝 {update.message.caption or '(без текста)'}"
                await update.get_bot().send_photo(
                    chat_id=admin_id,
                    photo=update.message.photo[-1].file_id,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                text = update.message.text or ""
                await update.get_bot().send_message(
                    chat_id=admin_id,
                    text=f"{header}\n\n📝 {text}",
                    parse_mode="HTML"
                )
        except Exception:
            pass

    await update.message.reply_text(
        t("complaint_sent", lang),
        parse_mode="HTML"
    )
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


def register_handlers(app: Application):
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("complaint", cmd_complaint),
            MessageHandler(
                filters.Regex("^(🚨 Жалоба|🚨 Shikoyat)$"),
                cmd_complaint
            ),
        ],
        states={
            WAITING_COMPLAINT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_complaint),
                MessageHandler(filters.PHOTO, receive_complaint),
                CallbackQueryHandler(handle_complaint_cancel, pattern="^complaint_cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )
    app.add_handler(conv)