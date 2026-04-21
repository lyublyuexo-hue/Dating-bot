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
        await update.message.reply_text(
            t("no_matches", lang)
        )
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

        # 👉 кнопка если есть username
        if other.username:
            buttons.append([
                InlineKeyboardButton(
                    t("write_to", lang, name=other.name),
                    url=f"https://t.me/{other.username}"
                )
            ])
        else:
            # 👉 fallback если нет username
            buttons.append([
                InlineKeyboardButton(
                    t("no_username", lang),
                    callback_data="no_username"
                )
            ])

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


def register_handlers(app: Application):
    app.add_handler(
        MessageHandler(
            filters.Regex("^(💌 Мои мэтчи|💌 Mos kelganlar)$"),
            show_matches
        )
    )