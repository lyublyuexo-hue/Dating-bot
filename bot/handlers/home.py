"""
Главный экран + Reply-кнопки меню:
- 👀 Смотреть анкеты
- 🔍 Поиск (только Premium)
- ⭐ Избранные
- 🔗 Реферал
- inline: home:browse / myprofile / stop / premium
- inline: premium:* / pay_confirm:*
- inline: search:* / search_tag:*
- inline: fav:* / fav_remove:* / fav_nav:*
- inline: lang:* — смена языка
"""
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from sqlalchemy import select, and_, func
from database.models import User, Like, Favorite, Premium, Referral, Tag, user_tags
from database.session import Session
from bot.keyboards.main import (
    home_inline_kb, main_menu_kb, search_mode_kb, search_tags_kb, premium_kb,
    like_skip_kb, favorites_item_kb, favorites_nav_kb, referral_kb,
    payment_confirm_kb, language_kb, CARD_NUMBER, PREMIUM_PLANS
)

from bot.services.user_service import UserService
from bot.modules.tags import TagModule
from bot.i18n import t
BOOST_EVERY = 3
FAVORITES_LIMIT_FREE = 10

MENU_ALL = {
    "👀 Смотреть анкеты", "👀 Anketalarni ko'rish",
    "🔍 Поиск", "🔍 Qidiruv",
    "⭐ Избранные", "⭐ Sevimlilar",
    "🔗 Реферал", "🔗 Referal",
    "👤 Мой профиль", "👤 Mening anketam",
}


async def _get_lang(user_id: int, ctx) -> str:
    lang = ctx.user_data.get("lang")
    if not lang:
        lang = await UserService.get_lang(user_id)
        ctx.user_data["lang"] = lang
    return lang


async def has_premium(user_id: int) -> bool:
    async with Session() as s:
        result = await s.execute(
            select(Premium).where(
                and_(Premium.user_id == user_id, Premium.expires_at > datetime.now())
            )
        )
        return result.scalar_one_or_none() is not None


# ══════════════════════════════════════════════════════════
# ГЛАВНЫЙ ЭКРАН
# ══════════════════════════════════════════════════════════

async def show_home(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = await UserService.get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text(t("profile_not_found", "ru"))
        return
    lang = await _get_lang(update.effective_user.id, ctx)
    await update.message.reply_text(
        t("home_text", lang),
        parse_mode="HTML",
        reply_markup=home_inline_kb(lang)
    )


async def handle_home(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    lang   = await _get_lang(update.effective_user.id, ctx)
    action = query.data.split(":")[1]

    if action == "browse":
        from bot.handlers.browsing import show_next_profile
        await show_next_profile(update, ctx)

    elif action == "myprofile":
        from bot.handlers.profile import show_profile
        await show_profile(update, ctx)

    elif action == "stop":
        await UserService.update_user(update.effective_user.id, is_active=False)
        await query.message.reply_text(t("home_hidden", lang))

    elif action == "premium":
        await query.message.reply_text(
            t("premium_text", lang),
            parse_mode="HTML",
            reply_markup=premium_kb(lang)
        )


# ══════════════════════════════════════════════════════════
# СМЕНА ЯЗЫКА
# ══════════════════════════════════════════════════════════

async def handle_language(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang  = query.data.split(":")[1]
    ctx.user_data["lang"] = lang
    await UserService.update_user(update.effective_user.id, lang=lang)
    key = "language_set_ru" if lang == "ru" else "language_set_uz"
    await query.message.reply_text(
        t(key, lang),
        reply_markup=main_menu_kb(lang)
    )


# ══════════════════════════════════════════════════════════
# PREMIUM — ОПЛАТА
# ══════════════════════════════════════════════════════════

async def handle_premium_plan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    lang   = await _get_lang(update.effective_user.id, ctx)
    plan   = query.data.split(":")[1]
    info   = PREMIUM_PLANS.get(plan, {})
    label  = info.get("label", {}).get(lang, "")
    price  = info.get("price", {}).get(lang, "")
    ctx.user_data["pending_plan"] = plan
    await query.message.reply_text(
        t("premium_payment", lang, label=label, price=price, card=CARD_NUMBER),
        parse_mode="HTML",
        reply_markup=payment_confirm_kb(plan, lang)
    )


async def handle_pay_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang  = await _get_lang(update.effective_user.id, ctx)
    plan  = query.data.split(":")[1]
    ctx.user_data["waiting_receipt"] = plan
    await query.message.reply_text(t("premium_awaiting_receipt", lang))

async def handle_receipt_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Если не ждём чек — передаём дальше (редактирование фото профиля)
    if not ctx.user_data.get("waiting_receipt"):
        from bot.handlers.profile import handle_edit_text
        await handle_edit_text(update, ctx)
        return

    plan = ctx.user_data.pop("waiting_receipt")
    lang = await _get_lang(update.effective_user.id, ctx)
    user = await UserService.get_user(update.effective_user.id)
    if not user:
        return

    info  = PREMIUM_PLANS.get(plan, {})
    label = info.get("label", {}).get(lang, plan)
    price = info.get("price", {}).get(lang, "")

    caption = (
        f"💳 <b>Новый чек на оплату Premium</b>\n\n"
        f"👤 {user.name} (@{user.username or 'нет'}) — "
        f"ID: <code>{user.telegram_id}</code>\n"
        f"📦 Тариф: {label} — {price}\n\n"
        f"Выдать: /admin → 👑 Выдать Premium\n"
        f"Затем введи: <code>{user.telegram_id} "
        f"{30 if plan == '1m' else 90 if plan == '3m' else 365}</code>"
    )

    for admin_id in settings.ADMIN_IDS:
        try:
            if update.message.photo:
                await ctx.bot.send_photo(
                    chat_id=admin_id,
                    photo=update.message.photo[-1].file_id,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                await ctx.bot.send_message(
                    chat_id=admin_id,
                    text=caption,
                    parse_mode="HTML"
                )
        except Exception:
            pass

    await update.message.reply_text(
        "✅ <b>Чек получен!</b>\n\n"
        "Платёж принят, ожидайте активации в течение "
        "<b>5–15 минут</b>.\n\n"
        "По вопросам: /complaint",
        parse_mode="HTML"
    )
    # Отправляем напрямую всем админам (не в группу)
    for admin_id in settings.ADMIN_IDS:
        try:
            if update.message.photo:
                await ctx.bot.send_photo(
                    chat_id=admin_id,
                    photo=update.message.photo[-1].file_id,
                    caption=caption,
                    parse_mode="HTML"
                )
            else:
                await ctx.bot.send_message(
                    chat_id=admin_id,
                    text=caption,
                    parse_mode="HTML"
                )
        except Exception:
            pass

    # Ответ пользователю
    await update.message.reply_text(
        "✅ <b>Чек получен!</b>\n\n"
        "Платёж принят, ожидайте активации в течение <b>5–15 минут</b>.\n\n"
        "По вопросам обратитесь через /complaint",
        parse_mode="HTML"
    )
# ══════════════════════════════════════════════════════════
# 👀 СМОТРЕТЬ АНКЕТЫ
# ══════════════════════════════════════════════════════════

async def browse_profiles(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.browsing import show_next_profile
    await show_next_profile(update, ctx)


# ══════════════════════════════════════════════════════════
# 🔍 ПОИСК
# ══════════════════════════════════════════════════════════

async def search_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = await _get_lang(update.effective_user.id, ctx)
    if not await has_premium(update.effective_user.id):
        await update.message.reply_text(t("search_premium_only", lang), parse_mode="HTML")
        return
    await update.message.reply_text(
        t("search_choose_mode", lang),
        parse_mode="HTML",
        reply_markup=search_mode_kb(lang)
    )


async def handle_search_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang  = await _get_lang(update.effective_user.id, ctx)
    mode  = query.data.split(":")[1]
    if mode == "tag":
        all_tags = await TagModule.get_all_tags()
        await query.message.reply_text(
            t("search_by_tag", lang),
            parse_mode="HTML",
            reply_markup=search_tags_kb(all_tags, lang)
        )
    elif mode == "city":
        ctx.user_data["waiting_city_search"] = True
        await query.message.reply_text(t("search_by_city", lang), parse_mode="HTML")


async def handle_search_tag(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    lang   = await _get_lang(update.effective_user.id, ctx)
    if not await has_premium(update.effective_user.id):
        await query.answer(t("search_premium_only", lang)[:200], show_alert=True)
        return
    tag_id = int(query.data.split(":")[1])
    async with Session() as s:
        tag  = await s.get(Tag, tag_id)
        result = await s.execute(
            select(User).join(user_tags, User.telegram_id == user_tags.c.user_id)
            .where(and_(
                user_tags.c.tag_id == tag_id,
                User.is_active == True,
                User.ban_status == "active",
                User.telegram_id != update.effective_user.id,
            )).limit(10)
        )
        users = result.scalars().all()

    tag_name = (tag.name_uz if lang == "uz" and tag.name_uz else tag.name)
    if not users:
        await query.message.reply_text(t("search_empty_tag", lang, tag=f"{tag.emoji or ''}{tag_name}"))
        return
    await query.message.reply_text(
        t("search_found_tag", lang, tag=f"{tag.emoji or ''}{tag_name}", count=len(users)),
        parse_mode="HTML"
    )
    for u in users:
        verified = t("browse_verified", lang) if u.verification_status == "verified" else ""
        caption  = f"<b>{u.name}, {u.age}</b> — {u.city}\n{verified}\n\n{u.about or ''}"
        if u.photo_file_id:
            await query.message.reply_photo(
                photo=u.photo_file_id, caption=caption,
                parse_mode="HTML", reply_markup=like_skip_kb(u.telegram_id, lang)
            )


async def handle_city_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_city_search"):
        return False   # не наш — пропускаем
    if update.message.text in MENU_ALL:
        return False
    ctx.user_data["waiting_city_search"] = False
    lang = await _get_lang(update.effective_user.id, ctx)
    city = update.message.text.strip()
    async with Session() as s:
        result = await s.execute(
            select(User).where(and_(
                User.city.ilike(f"%{city}%"),
                User.is_active == True,
                User.ban_status == "active",
                User.telegram_id != update.effective_user.id,
            )).limit(10)
        )
        users = result.scalars().all()
    if not users:
        await update.message.reply_text(t("search_empty_city", lang, city=city))
        return True
    await update.message.reply_text(
        t("search_found_city", lang, city=city, count=len(users)),
        parse_mode="HTML"
    )
    for u in users:
        verified = t("browse_verified", lang) if u.verification_status == "verified" else ""
        caption  = f"<b>{u.name}, {u.age}</b> — {u.city}\n{verified}\n\n{u.about or ''}"
        if u.photo_file_id:
            await update.message.reply_photo(
                photo=u.photo_file_id, caption=caption,
                parse_mode="HTML", reply_markup=like_skip_kb(u.telegram_id, lang)
            )
    return True


# ══════════════════════════════════════════════════════════
# ⭐ ИЗБРАННОЕ
# ══════════════════════════════════════════════════════════

async def show_favorites(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang    = await _get_lang(user_id, ctx)
    async with Session() as s:
        result = await s.execute(
            select(Favorite).where(Favorite.user_id == user_id).order_by(Favorite.created_at.desc())
        )
        favs = result.scalars().all()
    if not favs:
        await update.message.reply_text(t("favorites_empty", lang), parse_mode="HTML")
        return
    ctx.user_data["favorites"] = [f.target_id for f in favs]
    await _show_favorite_page(update, ctx, 0)


async def _show_favorite_page(update, ctx, index: int):
    user_id = update.effective_user.id
    lang    = await _get_lang(user_id, ctx)
    ids: list = ctx.user_data.get("favorites", [])
    if not ids or index >= len(ids):
        return
    target = await UserService.get_user(ids[index])
    if not target:
        return
    verified = t("browse_verified", lang) if target.verification_status == "verified" else ""
    caption  = t("favorites_caption", lang,
                 current=index + 1,
                 total=len(ids),
                 name=target.name,
                 age=target.age,
                 city=target.city,
                 verified=verified,
                 about=target.about or "")

    combined = InlineKeyboardMarkup(
        favorites_item_kb(target.telegram_id, lang).inline_keyboard +
        favorites_nav_kb(index, len(ids)).inline_keyboard
    )
    msg = update.message if hasattr(update, "message") and update.message else update.callback_query.message
    if target.photo_file_id:
        await msg.reply_photo(photo=target.photo_file_id, caption=caption, parse_mode="HTML", reply_markup=combined)
    else:
        await msg.reply_text(caption, parse_mode="HTML", reply_markup=combined)


async def handle_favorites_nav(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data.split(":")[1]
    if data == "noop":
        return
    await _show_favorite_page(update, ctx, int(data))


async def handle_fav_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    user_id   = update.effective_user.id
    target_id = int(query.data.split(":")[1])
    lang      = await _get_lang(user_id, ctx)

    async with Session() as s:
        existing = await s.execute(
            select(Favorite).where(and_(Favorite.user_id == user_id, Favorite.target_id == target_id))
        )
        if existing.scalar_one_or_none():
            await query.answer(t("fav_already", lang), show_alert=False)
            return
        if not await has_premium(user_id):
            count = (await s.execute(select(func.count()).where(Favorite.user_id == user_id))).scalar()
            if count >= FAVORITES_LIMIT_FREE:
                await query.answer(t("fav_limit", lang, limit=FAVORITES_LIMIT_FREE), show_alert=True)
                return
        s.add(Favorite(user_id=user_id, target_id=target_id))
        await s.commit()
    await query.answer(t("fav_added", lang), show_alert=False)


async def handle_fav_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    user_id   = update.effective_user.id
    target_id = int(query.data.split(":")[1])
    lang      = await _get_lang(user_id, ctx)

    async with Session() as s:
        result = await s.execute(
            select(Favorite).where(and_(Favorite.user_id == user_id, Favorite.target_id == target_id))
        )
        fav = result.scalar_one_or_none()
        if fav:
            await s.delete(fav)
            await s.commit()
    await query.answer(t("fav_removed", lang), show_alert=False)

    favs = ctx.user_data.get("favorites", [])
    if target_id in favs:
        favs.remove(target_id)
        ctx.user_data["favorites"] = favs
    if favs:
        await _show_favorite_page(update, ctx, 0)
    else:
        await query.message.reply_text(t("fav_list_empty", lang))


# ══════════════════════════════════════════════════════════
# 🔗 РЕФЕРАЛ
# ══════════════════════════════════════════════════════════

async def show_referral(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang    = await _get_lang(user_id, ctx)
    user    = await UserService.get_user(user_id)
    if not user:
        return

    if not user.referral_code:
        import hashlib
        code = hashlib.md5(str(user_id).encode()).hexdigest()[:8]
        await UserService.update_user(user_id, referral_code=code)
        user.referral_code = code

    async with Session() as s:
        count_result = await s.execute(select(func.count()).where(Referral.inviter_id == user_id))
        invited_count = count_result.scalar()

    next_boost_at = BOOST_EVERY - (invited_count % BOOST_EVERY)
    boost_text = ""
    if user.boost_until and user.boost_until > datetime.now():
        boost_text = t("referral_boost_active", lang, date=user.boost_until.strftime("%d.%m.%Y"))

    bot_info = await ctx.bot.get_me()
    await update.message.reply_text(
        t("referral_text", lang, invited=invited_count, next_boost=next_boost_at, boost_active=boost_text),
        parse_mode="HTML",
        reply_markup=referral_kb(bot_info.username, user.referral_code, lang)
    )
    link = f"https://t.me/{bot_info.username}?start=ref_{user.referral_code}"
    await update.message.reply_text(f"<code>{link}</code>", parse_mode="HTML")


# ══════════════════════════════════════════════════════════
# РЕГИСТРАЦИЯ ХЕНДЛЕРОВ
# ══════════════════════════════════════════════════════════

def register_handlers(app: Application):
    # Reply-кнопки меню (обе локали)
    from bot.handlers.profile import show_profile as _show_profile

    app.add_handler(MessageHandler(
        filters.Regex("^(👤 Мой профиль|👤 Mening anketam)$"),
        _show_profile
    ))
    app.add_handler(MessageHandler(
        filters.Regex("^(👀 Смотреть анкеты|👀 Anketalarni ko'rish)$"),
        browse_profiles
    ))
    app.add_handler(MessageHandler(
        filters.Regex("^(🔍 Поиск|🔍 Qidiruv)$"),
        search_menu
    ))
    app.add_handler(MessageHandler(
        filters.Regex("^(⭐ Избранные|⭐ Sevimlilar)$"),
        show_favorites
    ))
    app.add_handler(MessageHandler(
        filters.Regex("^(🔗 Реферал|🔗 Referal)$"),
        show_referral
    ))

    # Inline callbacks
    app.add_handler(CallbackQueryHandler(handle_home,          pattern="^home:"))
    app.add_handler(CallbackQueryHandler(handle_language,      pattern="^lang:"))
    app.add_handler(CallbackQueryHandler(handle_premium_plan,  pattern="^premium:"))
    app.add_handler(CallbackQueryHandler(handle_pay_confirm,   pattern="^pay_confirm:"))
    app.add_handler(CallbackQueryHandler(handle_search_mode,   pattern="^search:"))
    app.add_handler(CallbackQueryHandler(handle_search_tag,    pattern="^search_tag:"))
    app.add_handler(CallbackQueryHandler(handle_fav_add,       pattern="^fav:"))
    app.add_handler(CallbackQueryHandler(handle_fav_remove,    pattern="^fav_remove:"))
    app.add_handler(CallbackQueryHandler(handle_favorites_nav, pattern="^fav_nav:"))

    # Фото (чек оплаты) — только когда ждём
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt_photo))

    # Поиск по городу — текстовый ввод (без перехвата меню)
    async def _city_guard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return
        if update.message.text in MENU_ALL:
            return
        if ctx.user_data.get("edit_field"):  # пользователь редактирует профиль
            return
        if ctx.user_data.get("admin_mode"):  # админ вводит команду
            return
        await handle_city_input(update, ctx)

    def register_handlers(app: Application):
        app.add_handler(MessageHandler(
            filters.Regex("^(👀 Смотреть анкеты|👀 Anketalarni ko'rish)$"),
            browse_profiles
        ))
        app.add_handler(MessageHandler(
            filters.Regex("^(🔍 Поиск|🔍 Qidiruv)$"),
            search_menu
        ))
        app.add_handler(MessageHandler(
            filters.Regex("^(⭐ Избранные|⭐ Sevimlilar)$"),
            show_favorites
        ))
        app.add_handler(MessageHandler(
            filters.Regex("^(🔗 Реферал|🔗 Referal)$"),
            show_referral
        ))

        app.add_handler(CallbackQueryHandler(handle_home, pattern="^home:"))
        app.add_handler(CallbackQueryHandler(handle_language, pattern="^lang:"))
        app.add_handler(CallbackQueryHandler(handle_premium_plan, pattern="^premium:"))
        app.add_handler(CallbackQueryHandler(handle_pay_confirm, pattern="^pay_confirm:"))
        app.add_handler(CallbackQueryHandler(handle_search_mode, pattern="^search:"))
        app.add_handler(CallbackQueryHandler(handle_search_tag, pattern="^search_tag:"))
        app.add_handler(CallbackQueryHandler(handle_fav_add, pattern="^fav:"))
        app.add_handler(CallbackQueryHandler(handle_fav_remove, pattern="^fav_remove:"))
        app.add_handler(CallbackQueryHandler(handle_favorites_nav, pattern="^fav_nav:"))

        app.add_handler(MessageHandler(filters.PHOTO, handle_receipt_photo))

        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            _city_guard
        ))