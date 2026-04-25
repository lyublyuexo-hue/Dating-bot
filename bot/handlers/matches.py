from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from bot.services.match_service import MatchService
from bot.services.user_service import UserService
from bot.i18n import t


async def show_matches(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    user = await UserService.get_user(user_id)
    lang = user.lang if user else "ru"

    matches = await MatchService.get_matches(user_id)

    if not matches:
        await update.message.reply_text(t("no_matches", lang))
        return

    text = t("matches_title", lang) + "\n\n"
    buttons = []

    for m in matches:
        other_id = m.to_user_id if m.from_user_id == user_id else m.from_user_id
        other = await UserService.get_user(other_id)
        if not other:
            continue

        text += t("match_item", lang,
                  name=other.name,
                  age=other.age,
                  city=other.city) + "\n"

        # Кнопка "Написать" через deep link — работает без username
        write_label = t("write_to", lang, name=other.name)
        buttons.append([
            InlineKeyboardButton(
                write_label,
                url=f"tg://user?id={other.telegram_id}"
            )
        ])

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
    )


def register_handlers(app: Application):
    app.add_handler(
        MessageHandler(
            filters.Regex("^(💌 Мои мэтчи|💌 Mos kelganlar)$"),
            show_matches
        )
    )