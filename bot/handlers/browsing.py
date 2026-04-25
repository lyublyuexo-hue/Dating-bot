from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from bot.services.user_service import UserService
from bot.services.match_service import MatchService, LIMIT_FREE, LIMIT_REFERRAL, LIMIT_PREMIUM
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

    # ── Дневной лимит исчерпан ────────────────────────────────────────────
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

    # ── Анкет нет совсем ─────────────────────────────────────────────────
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


def _build_match_caption(person, viewer_lang: str, common_tags_text: str) -> str:
    """Строит текст матч-сообщения без бэкслешей в f-string."""
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

    lines = [
        header,
        "",
        f"<b>{person.name}, {person.age}</b> — {person.city}",
        person.about or "",
        "",
    ]

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
    """Кнопка 'Написать' через deep link — работает без username."""
    label = "✍️ Написать" if viewer_lang == "ru" else "✍️ Yozish"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, url=f"tg://user?id={person.telegram_id}")]
    ])


async def handle_like(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    liker_id  = update.effective_user.id
    target_id = int(query.data.split(":")[1])
    lang      = await _get_lang(liker_id, ctx)

    is_match = await MatchService.add_like(liker_id, target_id)

    # Антиспам: add_like возвращает None если уже лайкнули
    if is_match is None:
        already = "Вы уже лайкнули этого пользователя." if lang == "ru" else "Siz bu foydalanuvchini allaqachon layklagansiz."
        await query.answer(already, show_alert=False)
        await show_next_profile(update, ctx)
        return

    await RatingModule.add_points(liker_id, "like", 1)

    if not is_match:
        # Уведомляем target что кто-то лайкнул его профиль
        liker = await UserService.get_user(liker_id)
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
                InlineKeyboardButton(view_label, callback_data="home:browse")
            ]])
            try:
                if liker.photo_file_id:
                    await ctx.bot.send_photo(
                        chat_id=target_id,
                        photo=liker.photo_file_id,
                        caption=notif_text,
                        parse_mode="HTML",
                        reply_markup=notif_kb
                    )
                else:
                    await ctx.bot.send_message(
                        target_id, notif_text,
                        parse_mode="HTML", reply_markup=notif_kb
                    )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Не удалось отправить уведомление о лайке {target_id}: {e}")

    if is_match:
        liker  = await UserService.get_user(liker_id)
        target = await UserService.get_user(target_id)
        common = await MutualInterestsModule.get_common_tags(liker_id, target_id)

        def common_text(l):
            if not common:
                return ""
            tags = ", ".join(f"{tag.emoji or ''}{tag.name}" for tag in common)
            return t("match_common_tags", l, tags=tags)

        liker_lang  = lang
        target_lang = target.lang or "ru"

        caption_for_liker  = _build_match_caption(target, liker_lang,  common_text(liker_lang))
        caption_for_target = _build_match_caption(liker,  target_lang, common_text(target_lang))

        # Отправляем лайкнувшему анкету target
        try:
            kb = _match_write_kb(target, liker_lang)
            if target.photo_file_id:
                await ctx.bot.send_photo(
                    chat_id=liker_id,
                    photo=target.photo_file_id,
                    caption=caption_for_liker,
                    parse_mode="HTML",
                    reply_markup=kb
                )
            else:
                await ctx.bot.send_message(
                    liker_id, caption_for_liker,
                    parse_mode="HTML", reply_markup=kb
                )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Не удалось отправить матч лайкнувшему {liker_id}: {e}")

        # Отправляем target анкету лайкнувшего
        try:
            kb = _match_write_kb(liker, target_lang)
            if liker.photo_file_id:
                await ctx.bot.send_photo(
                    chat_id=target_id,
                    photo=liker.photo_file_id,
                    caption=caption_for_target,
                    parse_mode="HTML",
                    reply_markup=kb
                )
            else:
                await ctx.bot.send_message(
                    target_id, caption_for_target,
                    parse_mode="HTML", reply_markup=kb
                )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Не удалось отправить матч target {target_id}: {e}")

        await RatingModule.add_points(liker_id,  "match", 5)
        await RatingModule.add_points(target_id, "match", 5)
        await query.answer("🎉 Взаимная симпатия!", show_alert=True)
    else:
        await query.answer(t("like_sent", lang), show_alert=False)

    await show_next_profile(update, ctx)


async def handle_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang  = await _get_lang(update.effective_user.id, ctx)
    await query.answer(t("skipped", lang))
    await show_next_profile(update, ctx)


async def handle_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    await query.answer()
    lang      = await _get_lang(update.effective_user.id, ctx)
    target_id = int(query.data.split(":")[1])
    await query.message.reply_text(
        t("report_choose", lang),
        reply_markup=report_reason_kb(target_id, lang)
    )


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
    app.add_handler(CallbackQueryHandler(handle_like,          pattern="^like:"))
    app.add_handler(CallbackQueryHandler(handle_skip,          pattern="^skip:"))
    app.add_handler(CallbackQueryHandler(handle_report,        pattern="^report:"))
    app.add_handler(CallbackQueryHandler(handle_report_reason, pattern="^report_reason:"))