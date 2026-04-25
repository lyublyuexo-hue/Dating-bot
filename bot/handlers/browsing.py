from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from bot.services.user_service import UserService
from bot.services.match_service import MatchService, LIMIT_FREE, LIMIT_REFERRAL, LIMIT_PREMIUM
from bot.modules.mutual_interests import MutualInterestsModule
from bot.modules.rating import RatingModule
from bot.keyboards.main import like_skip_kb, report_reason_kb, home_inline_kb
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

    lang = await _get_lang(user_id, ctx)

    # ── Приоритет: показываем тех кто лайкнул ────────────────────────────
    pending = ctx.user_data.get("pending_likers", [])
    if pending:
        liker_id = pending.pop(0)
        ctx.user_data["pending_likers"] = pending
        ctx.user_data["from_pending"] = True

        profile = await UserService.get_user(liker_id)
        if profile and profile.is_active and profile.ban_status == "active":
            await _send_profile(message, profile, lang)
            return
        # Профиль удалён — берём следующего
        return await show_next_profile(update, ctx)

    ctx.user_data["from_pending"] = False

    # ── Обычная лента ─────────────────────────────────────────────────────
    profile = await MatchService.get_next_profile(user_id)

    if profile == "limit_reached":
        info = await MatchService.get_daily_limit_info(user_id)
        if lang == "uz":
            text = (
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "⏳  <b>Kunlik limit tugadi</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Bugun siz <b>{info['used']} ta</b> anketa ko'rdingiz.\n"
                f"Sizning limitingiz: <b>{info['limit']} ta/kun</b>\n\n"
                "🔓 <b>Limitni oshirish:</b>\n\n"
                f"👥  Do'st taklif qiling\n"
                f"     → kuniga <b>{LIMIT_REFERRAL} ta</b> anketa\n\n"
                f"⭐  Premium oling\n"
                f"     → kuniga <b>{LIMIT_PREMIUM} ta</b> anketa\n\n"
                "🌅  Ertaga qaytib keling!"
            )
        else:
            text = (
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "⏳  <b>Дневной лимит исчерпан</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Сегодня ты посмотрел <b>{info['used']}</b> анкет.\n"
                f"Твой лимит: <b>{info['limit']} анкет/день</b>\n\n"
                "🔓 <b>Как увеличить лимит:</b>\n\n"
                f"👥  Пригласи друга\n"
                f"     → <b>{LIMIT_REFERRAL} анкеты/день</b>\n\n"
                f"⭐  Купи Premium\n"
                f"     → <b>{LIMIT_PREMIUM} анкет/день</b>\n\n"
                "🌅  Возвращайся завтра!"
            )
        await message.reply_text(text, parse_mode="HTML")
        return

    if not profile:
        await message.reply_text(
            t("home_text", lang),
            parse_mode="HTML",
            reply_markup=home_inline_kb(lang)
        )
        return

    await _send_profile(message, profile, lang)


async def _send_profile(message, profile, lang: str):
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
        await message.reply_photo(photo=profile.photo_file_id, caption=caption,
                                  parse_mode="HTML", reply_markup=kb)
    else:
        await message.reply_text(caption, parse_mode="HTML", reply_markup=kb)


def _build_match_caption(person, viewer_lang: str, common_tags_text: str) -> str:
    if viewer_lang == "ru":
        header    = "🎉 <b>Взаимная симпатия!</b>"
        verified  = "✅ Верифицирован"
        write_lbl = "Написать"
        no_user   = "Нет username"
    else:
        header    = "🎉 <b>O'zaro yoqish!</b>"
        verified  = "✅ Tasdiqlangan"
        write_lbl = "Yozish"
        no_user   = "Username yo'q"

    lines = [header, "", f"<b>{person.name}, {person.age}</b> — {person.city}",
             person.about or "", ""]
    if person.verification_status == "verified":
        lines.append(verified)
    if person.username:
        lines.append(f"{write_lbl}: @{person.username}")
    else:
        lines.append(no_user)
    if common_tags_text:
        lines.append("")
        lines.append(common_tags_text)
    return "\n".join(lines)


def _match_write_kb(person, viewer_lang: str) -> InlineKeyboardMarkup:
    label = "✍️ Написать" if viewer_lang == "ru" else "✍️ Yozish"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, url=f"tg://user?id={person.telegram_id}")]
    ])


async def _after_action(update: Update, ctx: ContextTypes.DEFAULT_TYPE, lang: str):
    """После лайка/дизлайка — следующий из очереди или главное меню."""
    from_pending = ctx.user_data.get("from_pending", False)
    pending      = ctx.user_data.get("pending_likers", [])

    if from_pending and not pending:
        # Очередь лайкнувших закончилась → главное меню
        message = update.callback_query.message if update.callback_query else update.message
        await message.reply_text(
            t("home_text", lang),
            parse_mode="HTML",
            reply_markup=home_inline_kb(lang)
        )
        ctx.user_data["from_pending"] = False
        return

    await show_next_profile(update, ctx)


async def handle_browse_liker(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Кнопка из уведомления о лайке — показывает профиль лайкнувшего."""
    query    = update.callback_query
    await query.answer()
    liker_id = int(query.data.split(":")[1])

    pending = ctx.user_data.get("pending_likers", [])
    if liker_id not in pending:
        pending.insert(0, liker_id)
    ctx.user_data["pending_likers"] = pending
    ctx.user_data["from_pending"]   = True

    await show_next_profile(update, ctx)


async def handle_like(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    liker_id  = update.effective_user.id
    target_id = int(query.data.split(":")[1])
    lang      = await _get_lang(liker_id, ctx)

    is_match = await MatchService.add_like(liker_id, target_id)

    if is_match is None:
        already = "Вы уже лайкнули этого пользователя." if lang == "ru" else "Siz bu foydalanuvchini allaqachon layklagansiz."
        await query.answer(already, show_alert=False)
        await _after_action(update, ctx, lang)
        return

    await RatingModule.add_points(liker_id, "like", 1)

    if not is_match:
        liker  = await UserService.get_user(liker_id)
        target = await UserService.get_user(target_id)
        if liker and target:
            target_lang = target.lang or "ru"
            if target_lang == "uz":
                notif_text = (
                    f"❤️ <b>Kimdir sizni yoqtirdi!</b>\n\n"
                    f"<b>{liker.name}, {liker.age}</b> — {liker.city}\n\n"
                    f"Agar siz ham uni yoqtirsangiz — o'zaro yoqish bo'ladi! 🎉"
                )
            else:
                notif_text = (
                    f"❤️ <b>Кто-то лайкнул тебя!</b>\n\n"
                    f"<b>{liker.name}, {liker.age}</b> — {liker.city}\n\n"
                    f"Если лайкнешь в ответ — будет взаимная симпатия! 🎉"
                )
            view_label = "👀 Смотреть анкеты" if target_lang == "ru" else "👀 Anketalarni ko'rish"
            notif_kb = InlineKeyboardMarkup([[
                InlineKeyboardButton(view_label, callback_data=f"browse_liker:{liker_id}")
            ]])
            try:
                if liker.photo_file_id:
                    await ctx.bot.send_photo(chat_id=target_id, photo=liker.photo_file_id,
                                             caption=notif_text, parse_mode="HTML", reply_markup=notif_kb)
                else:
                    await ctx.bot.send_message(target_id, notif_text,
                                               parse_mode="HTML", reply_markup=notif_kb)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Уведомление о лайке {target_id}: {e}")

    if is_match:
        liker  = await UserService.get_user(liker_id)
        target = await UserService.get_user(target_id)
        common = await MutualInterestsModule.get_common_tags(liker_id, target_id)

        def common_text(l):
            if not common:
                return ""
            return t("match_common_tags", l, tags=", ".join(f"{t.emoji or ''}{t.name}" for t in common))

        liker_lang  = lang
        target_lang = target.lang or "ru"

        try:
            kb = _match_write_kb(target, liker_lang)
            caption = _build_match_caption(target, liker_lang, common_text(liker_lang))
            if target.photo_file_id:
                await ctx.bot.send_photo(chat_id=liker_id, photo=target.photo_file_id,
                                         caption=caption, parse_mode="HTML", reply_markup=kb)
            else:
                await ctx.bot.send_message(liker_id, caption, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Матч лайкнувшему {liker_id}: {e}")

        try:
            kb = _match_write_kb(liker, target_lang)
            caption = _build_match_caption(liker, target_lang, common_text(target_lang))
            if liker.photo_file_id:
                await ctx.bot.send_photo(chat_id=target_id, photo=liker.photo_file_id,
                                         caption=caption, parse_mode="HTML", reply_markup=kb)
            else:
                await ctx.bot.send_message(target_id, caption, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Матч target {target_id}: {e}")

        await RatingModule.add_points(liker_id,  "match", 5)
        await RatingModule.add_points(target_id, "match", 5)
        await query.answer("🎉 Взаимная симпатия!", show_alert=True)
    else:
        await query.answer(t("like_sent", lang), show_alert=False)

    await _after_action(update, ctx, lang)


async def handle_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang  = await _get_lang(update.effective_user.id, ctx)
    await query.answer(t("skipped", lang))
    await _after_action(update, ctx, lang)


async def handle_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    await query.answer()
    lang      = await _get_lang(update.effective_user.id, ctx)
    target_id = int(query.data.split(":")[1])
    await query.message.reply_text(t("report_choose", lang),
                                   reply_markup=report_reason_kb(target_id, lang))


async def handle_report_reason(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    lang   = await _get_lang(update.effective_user.id, ctx)
    parts  = query.data.split(":")
    target_id    = int(parts[1])
    reason_index = int(parts[2])
    reasons      = t("report_reasons", lang)
    reason_text  = reasons[reason_index] if reason_index < len(reasons) else "Другое"

    reporter      = await UserService.get_user(update.effective_user.id)
    reporter_name = reporter.name if reporter else str(update.effective_user.id)

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
    app.add_handler(CallbackQueryHandler(handle_browse_liker,  pattern="^browse_liker:"))
    app.add_handler(CallbackQueryHandler(handle_like,          pattern="^like:"))
    app.add_handler(CallbackQueryHandler(handle_skip,          pattern="^skip:"))
    app.add_handler(CallbackQueryHandler(handle_report,        pattern="^report:"))
    app.add_handler(CallbackQueryHandler(handle_report_reason, pattern="^report_reason:"))
