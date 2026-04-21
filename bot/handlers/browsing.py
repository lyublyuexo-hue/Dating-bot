from datetime import datetime
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from bot.services.user_service import UserService
from bot.services.match_service import MatchService
from bot.modules.mutual_interests import MutualInterestsModule
from bot.modules.rating import RatingModule
from bot.keyboards.main import like_skip_kb, report_reason_kb
from bot.i18n import t
from config import settings


async def _get_lang(user_id: int, ctx) -> str:
    lang = ctx.user_data.get("lang")
    if not lang:
        lang = await UserService.get_lang(user_id)
        ctx.user_data["lang"] = lang
    return lang


async def show_next_profile(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        message = update.callback_query.message
        user_id = update.callback_query.from_user.id
    else:
        message = update.message
        user_id = update.effective_user.id

    lang    = await _get_lang(user_id, ctx)
    profile = await MatchService.get_next_profile(user_id)

    if not profile:
        await message.reply_text(t("browse_empty", lang))
        return

    boost_badge = "🚀 " if (profile.boost_until and profile.boost_until > datetime.now()) else ""
    verified    = t("browse_verified", lang) if profile.verification_status == "verified" else ""
    tags_text   = ", ".join(
        f"{tag.emoji or ''}{tag.name_uz if lang == 'uz' and tag.name_uz else tag.name}"
        for tag in profile.tags
    ) or t("browse_no_tags", lang)

    caption = t("browse_caption", lang,
                boost=boost_badge,
                name=profile.name,
                age=profile.age,
                city=profile.city,
                verified=verified,
                about=profile.about or "",
                tags=tags_text)

    kb = like_skip_kb(profile.telegram_id, lang)

    if profile.photo_file_id:
        await message.reply_photo(
            photo=profile.photo_file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=kb
        )
    else:
        await message.reply_text(caption, parse_mode="HTML", reply_markup=kb)


async def handle_like(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    liker_id  = update.effective_user.id
    target_id = int(query.data.split(":")[1])
    lang      = await _get_lang(liker_id, ctx)

    is_match = await MatchService.add_like(liker_id, target_id)
    await RatingModule.add_points(liker_id, "like", 1)

    if is_match:
        liker  = await UserService.get_user(liker_id)
        target = await UserService.get_user(target_id)
        common = await MutualInterestsModule.get_common_tags(liker_id, target_id)

        def common_text(l):
            if not common:
                return ""
            tags = ", ".join(f"{tag.emoji or ''}{tag.name}" for tag in common)
            return t("match_common_tags", l, tags=tags)

        liker_uname  = liker.username  or t("match_username_none", lang)
        target_uname = target.username or t("match_username_none", lang)

        await ctx.bot.send_message(
            liker_id,
            t("match_notify", lang,
              name=target.name, username=target_uname, common=common_text(lang)),
            parse_mode="HTML"
        )
        target_lang = target.lang or "ru"
        await ctx.bot.send_message(
            target_id,
            t("match_notify", target_lang,
              name=liker.name, username=liker_uname, common=common_text(target_lang)),
            parse_mode="HTML"
        )
        await RatingModule.add_points(liker_id,  "match", 5)
        await RatingModule.add_points(target_id, "match", 5)
        await query.answer()
    else:
        await query.answer(t("like_sent", lang), show_alert=False)

    await show_next_profile(update, ctx)


async def handle_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang  = await _get_lang(update.effective_user.id, ctx)
    await query.answer(t("skipped", lang))
    await show_next_profile(update, ctx)


async def handle_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показать причины жалобы."""
    query     = update.callback_query
    await query.answer()
    lang      = await _get_lang(update.effective_user.id, ctx)
    target_id = int(query.data.split(":")[1])
    await query.message.reply_text(
        t("report_choose", lang),
        reply_markup=report_reason_kb(target_id, lang)
    )


async def handle_report_reason(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Жалоба — просто уведомляем админов, без сохранения в БД."""
    query  = update.callback_query
    await query.answer()
    lang   = await _get_lang(update.effective_user.id, ctx)
    parts  = query.data.split(":")
    target_id    = int(parts[1])
    reason_index = int(parts[2])
    reasons      = t("report_reasons", lang)
    reason_text  = reasons[reason_index] if reason_index < len(reasons) else "Другое"

    reporter = await UserService.get_user(update.effective_user.id)
    reporter_name = reporter.name if reporter else str(update.effective_user.id)

    # Уведомляем всех админов
    msg = (
        f"🚨 <b>Жалоба</b>\n\n"
        f"От: {reporter_name} (<code>{update.effective_user.id}</code>)\n"
        f"На: <code>{target_id}</code>\n"
        f"Причина: {reason_text}"
    )
    for admin_id in settings.ADMIN_IDS:
        try:
            await ctx.bot.send_message(admin_id, msg, parse_mode="HTML")
        except Exception:
            pass

    await query.message.reply_text(t("report_sent", lang))
    await show_next_profile(update, ctx)


def register_handlers(app: Application):
    app.add_handler(CallbackQueryHandler(handle_like,          pattern="^like:"))
    app.add_handler(CallbackQueryHandler(handle_skip,          pattern="^skip:"))
    app.add_handler(CallbackQueryHandler(handle_report,        pattern="^report:"))
    app.add_handler(CallbackQueryHandler(handle_report_reason, pattern="^report_reason:"))