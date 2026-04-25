"""
Главный экран + Reply-кнопки меню:
- 👀 Смотреть анкеты
- 🔍 Поиск (только Premium) + фильтр по возрасту
- ⭐ Избранные
- 🔗 Реферал
- 🚫 Чёрный список (Premium)
- inline: home:browse / myprofile / stop / premium
- inline: premium:* / pay_confirm:*
- inline: search:* / search_tag:* / search_age:*
- inline: fav:* / fav_remove:* / fav_nav:*
- inline: lang:* — смена языка
- inline: blacklist:* / unblacklist:*
- Кнопка "Написать" через tg://user?id=... deep link
"""

from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from sqlalchemy import select, and_, func
from database.models import User, Like, Favorite, Premium, Referral, Tag, user_tags, BlackList
from database.session import Session
from bot.keyboards.main import (
    home_inline_kb, main_menu_kb, search_mode_kb, search_tags_kb, premium_kb,
    like_skip_kb, favorites_item_kb, favorites_nav_kb, referral_kb,
    payment_confirm_kb, language_kb, CARD_NUMBER, PREMIUM_PLANS
)
from bot.services.user_service import UserService
from bot.services.match_service import MatchService
from bot.modules.tags import TagModule
from bot.i18n import t
from config import settings

BOOST_EVERY = 3
FAVORITES_LIMIT_FREE = 10

MENU_ALL = {
    "👀 Смотреть анкеты", "👀 Anketalarni ko'rish",
    "🔍 Поиск", "🔍 Qidiruv",
    "⭐ Избранные", "⭐ Sevimlilar",
    "🔗 Реферал", "🔗 Referal",
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
    query = update.callback_query
    await query.answer()
    lang = await _get_lang(update.effective_user.id, ctx)
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
    lang = query.data.split(":")[1]
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
    query = update.callback_query
    await query.answer()
    lang = await _get_lang(update.effective_user.id, ctx)
    plan = query.data.split(":")[1]
    info = PREMIUM_PLANS.get(plan, {})
    label = info.get("label", {}).get(lang, "")
    price = info.get("price", {}).get(lang, "")
    ctx.user_data["pending_plan"] = plan
    await query.message.reply_text(
        t("premium_payment", lang, label=label, price=price, card=CARD_NUMBER),
        parse_mode="HTML",
        reply_markup=payment_confirm_kb(plan, lang)
    )


async def handle_pay_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await _get_lang(update.effective_user.id, ctx)
    plan = query.data.split(":")[1]
    ctx.user_data["waiting_receipt"] = plan
    await query.message.reply_text(t("premium_awaiting_receipt", lang))


async def handle_receipt_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_receipt"):
        return

    plan = ctx.user_data.pop("waiting_receipt")
    lang = await _get_lang(update.effective_user.id, ctx)
    user = await UserService.get_user(update.effective_user.id)
    if not user:
        return

    info = PREMIUM_PLANS.get(plan, {})
    label = info.get("label", {}).get(lang, plan)
    price = info.get("price", {}).get(lang, "")
    days = 30 if plan == "1m" else 90 if plan == "3m" else 365

    caption = (
        f"💳 <b>Новый чек на оплату Premium</b>\n\n"
        f"👤 {user.name} (@{user.username or 'нет'}) — "
        f"ID: <code>{user.telegram_id}</code>\n"
        f"📦 Тариф: {label} — {price}\n\n"
        f"Выдать: /admin → 👑 Выдать Premium\n"
        f"Затем введи: <code>{user.telegram_id} {days}</code>"
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
        "Платёж принят, ожидайте активации в течение <b>5–15 минут</b>.\n\n"
        "По вопросам обратитесь через /complaint",
        parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════
# 👀 СМОТРЕТЬ АНКЕТЫ
# ══════════════════════════════════════════════════════════

async def browse_profiles(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = await _get_lang(update.effective_user.id, ctx)
    await update.message.reply_text(
        t("home_text", lang),
        parse_mode="HTML",
        reply_markup=home_inline_kb(lang)
    )


# ══════════════════════════════════════════════════════════
# 🔍 ПОИСК + ФИЛЬТР ВОЗРАСТА (Premium)
# ══════════════════════════════════════════════════════════

def _search_menu_kb(lang: str, age_min=None, age_max=None) -> InlineKeyboardMarkup:
    """Клавиатура поиска с кнопкой фильтра возраста."""
    age_label = (
        f"🎂 {age_min}–{age_max}" if age_min and age_max
        else ("🎂 Возраст" if lang == "ru" else "🎂 Yosh")
    )
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏷 По тегу" if lang == "ru" else "🏷 Teg bo'yicha",
                callback_data="search:tag"
            ),
            InlineKeyboardButton(
                "🏙 По городу" if lang == "ru" else "🏙 Shahar bo'yicha",
                callback_data="search:city"
            ),
        ],
        [
            InlineKeyboardButton(age_label, callback_data="search:age_filter"),
        ],
    ])


async def search_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = await _get_lang(update.effective_user.id, ctx)
    user_id = update.effective_user.id
    if not await has_premium(user_id):
        await update.message.reply_text(t("search_premium_only", lang), parse_mode="HTML")
        return

    age_min, age_max = await MatchService.get_search_age_filter(user_id)
    await update.message.reply_text(
        t("search_choose_mode", lang),
        parse_mode="HTML",
        reply_markup=_search_menu_kb(lang, age_min, age_max)
    )


async def handle_search_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await _get_lang(update.effective_user.id, ctx)
    mode = query.data.split(":")[1]

    if mode == "age_filter":
        # Запрашиваем ввод возраста
        ctx.user_data["waiting_age_filter"] = True
        text = (
            "🎂 Введите диапазон возраста в формате: <b>18-35</b>\n\n"
            "Например: <code>20-30</code>"
            if lang == "ru" else
            "🎂 Yosh diapazonini kiriting: <b>18-35</b>\n\n"
            "Masalan: <code>20-30</code>"
        )
        await query.message.reply_text(text, parse_mode="HTML")
        return

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


async def handle_age_filter_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """Обрабатывает ввод фильтра возраста. Возвращает True если обработал."""
    if not ctx.user_data.get("waiting_age_filter"):
        return False
    if update.message.text in MENU_ALL:
        return False

    ctx.user_data["waiting_age_filter"] = False
    lang = await _get_lang(update.effective_user.id, ctx)
    user_id = update.effective_user.id

    text = update.message.text.strip()
    try:
        parts = text.replace(" ", "").split("-")
        age_min = int(parts[0])
        age_max = int(parts[1])
        if age_min < 14 or age_max > 99 or age_min > age_max:
            raise ValueError
    except Exception:
        err = (
            "❌ Неверный формат. Введите, например: <code>18-35</code>"
            if lang == "ru" else
            "❌ Noto'g'ri format. Masalan: <code>18-35</code>"
        )
        await update.message.reply_text(err, parse_mode="HTML")
        return True

    await MatchService.save_search_age_filter(user_id, age_min, age_max)
    ok = (
        f"✅ Фильтр возраста установлен: <b>{age_min}–{age_max}</b>"
        if lang == "ru" else
        f"✅ Yosh filtri o'rnatildi: <b>{age_min}–{age_max}</b>"
    )
    await update.message.reply_text(
        ok,
        parse_mode="HTML",
        reply_markup=_search_menu_kb(lang, age_min, age_max)
    )
    return True


async def handle_search_tag(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = await _get_lang(update.effective_user.id, ctx)
    user_id = update.effective_user.id

    if not await has_premium(user_id):
        await query.answer(t("search_premium_only", lang)[:200], show_alert=True)
        return

    tag_id = int(query.data.split(":")[1])
    age_min, age_max = await MatchService.get_search_age_filter(user_id)

    async with Session() as s:
        tag = await s.get(Tag, tag_id)
        tag_name = (tag.name_uz if lang == "uz" and tag.name_uz else tag.name)

    users = await MatchService.search_by_tag_filtered(user_id, tag_id, age_min, age_max)

    if not users:
        await query.message.reply_text(t("search_empty_tag", lang, tag=f"{tag.emoji or ''}{tag_name}"))
        return

    await query.message.reply_text(
        t("search_found_tag", lang, tag=f"{tag.emoji or ''}{tag_name}", count=len(users)),
        parse_mode="HTML"
    )
    for u in users:
        await _send_search_result(query.message, u, lang, user_id)


async def handle_city_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("waiting_city_search"):
        return False
    if update.message.text in MENU_ALL:
        return False

    ctx.user_data["waiting_city_search"] = False
    lang = await _get_lang(update.effective_user.id, ctx)
    user_id = update.effective_user.id
    city = update.message.text.strip()
    age_min, age_max = await MatchService.get_search_age_filter(user_id)

    users = await MatchService.search_by_city_filtered(user_id, city, age_min, age_max)

    if not users:
        await update.message.reply_text(t("search_empty_city", lang, city=city))
        return True

    await update.message.reply_text(
        t("search_found_city", lang, city=city, count=len(users)),
        parse_mode="HTML"
    )
    for u in users:
        await _send_search_result(update.message, u, lang, user_id)
    return True


async def _send_search_result(msg, u: User, lang: str, viewer_id: int):
    """
    Отправляет карточку анкеты с кнопками лайк/пропустить/написать/в чёрный список.
    Кнопка 'Написать' — deep link tg://user?id=USER_ID (работает без username).
    """
    verified = t("browse_verified", lang) if u.verification_status == "verified" else ""
    caption = f"<b>{u.name}, {u.age}</b> — {u.city}\n{verified}\n\n{u.about or ''}"

    # Кнопка "Написать" через deep link
    write_label = "✍️ Написать" if lang == "ru" else "✍️ Yozish"
    bl_label    = "🚫 В ЧС"     if lang == "ru" else "🚫 Qora ro'yxat"

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❤️", callback_data=f"like:{u.telegram_id}"),
            InlineKeyboardButton("👎", callback_data=f"skip:{u.telegram_id}"),
            InlineKeyboardButton(write_label, url=f"tg://user?id={u.telegram_id}"),
        ],
        [
            InlineKeyboardButton(bl_label, callback_data=f"blacklist:{u.telegram_id}"),
        ],
    ])

    if u.photo_file_id:
        await msg.reply_photo(photo=u.photo_file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
    else:
        await msg.reply_text(caption, parse_mode="HTML", reply_markup=kb)


# ══════════════════════════════════════════════════════════
# ⭐ ИЗБРАННОЕ
# ══════════════════════════════════════════════════════════

async def show_favorites(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = await _get_lang(user_id, ctx)
    try:
        async with Session() as s:
            result = await s.execute(
                select(Favorite).where(Favorite.user_id == user_id).order_by(Favorite.created_at.desc())
            )
            favs = result.scalars().all()
            fav_ids = [f.target_id for f in favs]

        if not fav_ids:
            await update.message.reply_text(t("favorites_empty", lang), parse_mode="HTML")
            return

        ctx.user_data["favorites"] = fav_ids
        await _show_favorite_page(update, ctx, 0)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"show_favorites error: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Ошибка загрузки избранного. Попробуйте ещё раз.")


async def _show_favorite_page(update, ctx, index: int):
    import logging
    user_id = update.effective_user.id
    lang = await _get_lang(user_id, ctx)
    ids: list = ctx.user_data.get("favorites", [])
    if not ids or index >= len(ids):
        return

    try:
        target = await UserService.get_user(ids[index])
    except Exception as e:
        logging.getLogger(__name__).error(f"_show_favorite_page get_user error: {e}", exc_info=True)
        return
    if not target:
        return

    has_vip = await MatchService.has_vip(user_id)
    is_premium = await has_premium(user_id)
    verified = t("browse_verified", lang) if target.verification_status == "verified" else ""
    caption = t("favorites_caption", lang,
                current=index + 1,
                total=len(ids),
                name=target.name,
                age=target.age,
                city=target.city,
                verified=verified,
                about=target.about or "")

    bl_label = "🚫 В ЧС" if lang == "ru" else "🚫 Qora ro'yxat"

    extra_rows = []
    if is_premium:
        extra_rows.append([InlineKeyboardButton(bl_label, callback_data=f"blacklist:{target.telegram_id}")])
    if has_vip:
        extra_rows.append([
            InlineKeyboardButton(
                "💎 Запросить контакт" if lang == "ru" else "💎 Aloqa so'rash",
                callback_data=f"vip_contact:{target.telegram_id}"
            )
        ])

    all_rows = (
        list(favorites_item_kb(target.telegram_id, lang, has_vip=False).inline_keyboard)
        + extra_rows
        + list(favorites_nav_kb(index, len(ids)).inline_keyboard)
    )
    combined = InlineKeyboardMarkup(all_rows)

    msg = update.message if hasattr(update, "message") and update.message else update.callback_query.message
    if target.photo_file_id:
        await msg.reply_photo(photo=target.photo_file_id, caption=caption, parse_mode="HTML", reply_markup=combined)
    else:
        await msg.reply_text(caption, parse_mode="HTML", reply_markup=combined)


async def handle_vip_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    await query.answer()
    user_id   = update.effective_user.id
    target_id = int(query.data.split(":")[1])
    lang      = await _get_lang(user_id, ctx)

    if not await MatchService.has_vip(user_id):
        txt = "💎 Эта функция только для VIP Premium." if lang == "ru" else "💎 Bu funksiya faqat VIP Premium uchun."
        await query.answer(txt, show_alert=True)
        return

    if not await MatchService.can_use_vip_contact(user_id):
        txt = "⏳ Вы уже использовали запрос в этом месяце." if lang == "ru" else "⏳ Siz bu oyda allaqachon so'rov yubordingiz."
        await query.answer(txt, show_alert=True)
        return

    requester = await UserService.get_user(user_id)
    target    = await UserService.get_user(target_id)

    msg = (
        f"💎 <b>VIP запрос личного контакта</b>\n\n"
        f"От: {requester.name} (@{requester.username or 'нет'}) — <code>{user_id}</code>\n"
        f"К: {target.name} (@{target.username or 'нет'}) — <code>{target_id}</code>\n\n"
        f"Передайте контакт вручную если оба согласны."
    )
    for admin_id in settings.ADMIN_IDS:
        try:
            await ctx.bot.send_message(admin_id, msg, parse_mode="HTML")
        except Exception:
            pass

    await MatchService.mark_vip_contact_used(user_id)
    txt = (
        "✅ Запрос отправлен администратору!" if lang == "ru"
        else "✅ So'rov administratorga yuborildi!"
    )
    await query.message.reply_text(txt, parse_mode="HTML")


async def handle_favorites_nav(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")[1]
    if data == "noop":
        return
    await _show_favorite_page(update, ctx, int(data))


async def handle_fav_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    target_id = int(query.data.split(":")[1])
    lang = await _get_lang(user_id, ctx)

    async with Session() as s:
        existing = await s.execute(
            select(Favorite).where(and_(Favorite.user_id == user_id, Favorite.target_id == target_id))
        )
        if existing.scalar_one_or_none():
            await query.message.reply_text(t("fav_already", lang))
            return

        if not await has_premium(user_id):
            count = (await s.execute(select(func.count()).where(Favorite.user_id == user_id))).scalar()
            if count >= FAVORITES_LIMIT_FREE:
                await query.message.reply_text(t("fav_limit", lang, limit=FAVORITES_LIMIT_FREE))
                return

        s.add(Favorite(user_id=user_id, target_id=target_id))
        await s.commit()
    await query.message.reply_text(t("fav_added", lang))


async def handle_fav_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    target_id = int(query.data.split(":")[1])
    lang = await _get_lang(user_id, ctx)

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
# 🚫 ЧЁРНЫЙ СПИСОК (Premium)
# ══════════════════════════════════════════════════════════

async def handle_blacklist_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Добавить пользователя в чёрный список (только Premium)."""
    query = update.callback_query
    await query.answer()
    user_id   = update.effective_user.id
    target_id = int(query.data.split(":")[1])
    lang      = await _get_lang(user_id, ctx)

    if not await has_premium(user_id):
        txt = (
            "🚫 Чёрный список доступен только для Premium." if lang == "ru"
            else "🚫 Qora ro'yxat faqat Premium uchun mavjud."
        )
        await query.answer(txt, show_alert=True)
        return

    added = await MatchService.add_to_blacklist(user_id, target_id)
    if added:
        txt = "🚫 Пользователь добавлен в чёрный список." if lang == "ru" else "🚫 Foydalanuvchi qora ro'yxatga qo'shildi."
    else:
        txt = "Уже в чёрном списке." if lang == "ru" else "Allaqachon qora ro'yxatda."
    await query.answer(txt, show_alert=True)


async def handle_blacklist_remove(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Убрать пользователя из чёрного списка."""
    query = update.callback_query
    await query.answer()
    user_id   = update.effective_user.id
    target_id = int(query.data.split(":")[1])
    lang      = await _get_lang(user_id, ctx)

    removed = await MatchService.remove_from_blacklist(user_id, target_id)
    txt = (
        ("✅ Удалён из чёрного списка." if removed else "Не найден в чёрном списке.")
        if lang == "ru" else
        ("✅ Qora ro'yxatdan o'chirildi." if removed else "Qora ro'yxatda topilmadi.")
    )
    await query.answer(txt, show_alert=True)


async def show_blacklist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показать чёрный список пользователя."""
    user_id = update.effective_user.id
    lang = await _get_lang(user_id, ctx)

    if not await has_premium(user_id):
        txt = (
            "🚫 Чёрный список доступен только для Premium." if lang == "ru"
            else "🚫 Qora ro'yxat faqat Premium uchun mavjud."
        )
        await update.message.reply_text(txt, parse_mode="HTML")
        return

    bl = await MatchService.get_blacklist(user_id)
    if not bl:
        txt = "Ваш чёрный список пуст." if lang == "ru" else "Qora ro'yxatingiz bo'sh."
        await update.message.reply_text(txt)
        return

    buttons = []
    for entry in bl:
        target = await UserService.get_user(entry.target_id)
        if not target:
            continue
        name = f"{target.name}, {target.age}"
        buttons.append([
            InlineKeyboardButton(
                f"❌ {name}",
                callback_data=f"unblacklist:{entry.target_id}"
            )
        ])

    header = "🚫 <b>Чёрный список</b>\n\nНажмите ❌ чтобы удалить:" if lang == "ru" else \
             "🚫 <b>Qora ro'yxat</b>\n\n❌ bosib o'chirish:"
    await update.message.reply_text(
        header,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ══════════════════════════════════════════════════════════
# 🔗 РЕФЕРАЛ
# ══════════════════════════════════════════════════════════

async def show_referral(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = await _get_lang(user_id, ctx)
    user = await UserService.get_user(user_id)
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
    app.add_handler(MessageHandler(
        filters.Regex("^(🚫 Чёрный список|🚫 Qora ro'yxat)$"),
        show_blacklist
    ))

    app.add_handler(CallbackQueryHandler(handle_home,           pattern="^home:"))
    app.add_handler(CallbackQueryHandler(handle_language,       pattern="^lang:"))
    app.add_handler(CallbackQueryHandler(handle_premium_plan,   pattern="^premium:"))
    app.add_handler(CallbackQueryHandler(handle_pay_confirm,    pattern="^pay_confirm:"))
    app.add_handler(CallbackQueryHandler(handle_search_mode,    pattern="^search:"))
    app.add_handler(CallbackQueryHandler(handle_search_tag,     pattern="^search_tag:"))
    app.add_handler(CallbackQueryHandler(handle_fav_add,        pattern="^fav:"))
    app.add_handler(CallbackQueryHandler(handle_fav_remove,     pattern="^fav_remove:"))
    app.add_handler(CallbackQueryHandler(handle_favorites_nav,  pattern="^fav_nav:"))
    app.add_handler(CallbackQueryHandler(handle_vip_contact,    pattern="^vip_contact:"))
    app.add_handler(CallbackQueryHandler(handle_blacklist_add,  pattern="^blacklist:"))
    app.add_handler(CallbackQueryHandler(handle_blacklist_remove, pattern="^unblacklist:"))

    # Справочник
    async def show_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        lang = await _get_lang(update.effective_user.id, ctx)
        try:
            await update.message.delete()
        except Exception:
            pass
        if lang == "uz":
            text = (
                "📖 <b>Qo'llanma</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🔘 <b>Tugmalar nima qiladi?</b>\n\n"
                "👀 <b>Anketalarni ko'rish</b> — yangi anketalar ko'rsatiladi\n"
                "🔍 <b>Qidiruv</b> — shahar yoki teg bo'yicha qidirish (Premium)\n"
                "⭐ <b>Sevimlilar</b> — saqlangan anketalar ro'yxati\n"
                "🔗 <b>Referal</b> — do'st taklif qilish va bonus olish\n"
                "🚫 <b>Qora ro'yxat</b> — foydalanuvchini yashirish (Premium)\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "❤️ — layk qo'yish\n"
                "👎 — o'tkazib yuborish\n"
                "⭐ — sevimlilarga qo'shish\n"
                "✍️ — to'g'ridan-to'g'ri yozish\n"
                "🚨 — shikoyat yuborish\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "💳 <b>To'lov va qaytarish</b>\n\n"
                "⚠️ Premium xarid qilingandan keyin <b>qaytarish mumkin emas</b>.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🚫 <b>Bloklash qoidalari</b>\n\n"
                "• <b>Oddiy qoidabuzarlik</b> — pul evaziga blokdan chiqarish mumkin.\n"
                "• <b>Og'ir qoidabuzarlik</b> — profil hech qachon blokdan chiqarilmaydi.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 <b>VIP Premium</b>\n\n"
                "Oyiga bir marta sevimlilaridagi profildan admin orqali aloqa so'rash mumkin.\n"
                "Narxi: 3 000 000 so'm/yil\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "❓ Savollar uchun: /complaint"
            )
        else:
            text = (
                "📖 <b>Справочник</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🔘 <b>Что делают кнопки?</b>\n\n"
                "👀 <b>Смотреть анкеты</b> — листать новые анкеты\n"
                "🔍 <b>Поиск</b> — поиск по городу или тегу (Premium)\n"
                "⭐ <b>Избранные</b> — сохранённые анкеты\n"
                "🔗 <b>Реферал</b> — пригласить друга и получить бонус\n"
                "🚫 <b>Чёрный список</b> — скрыть пользователя (Premium)\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "❤️ — поставить лайк\n"
                "👎 — пропустить анкету\n"
                "⭐ — добавить в избранное\n"
                "✍️ — написать напрямую\n"
                "🚨 — пожаловаться на пользователя\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "💳 <b>Оплата и возврат</b>\n\n"
                "⚠️ После оплаты Premium <b>возврат невозможен</b>.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🚫 <b>Правила блокировки</b>\n\n"
                "• <b>Обычное нарушение</b> — разблокировка возможна за оплату.\n"
                "• <b>Серьёзное нарушение</b> — профиль не будет разблокирован никогда.\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "💎 <b>VIP Premium</b>\n\n"
                "Раз в месяц можно запросить личный контакт через избранное.\n"
                "Стоимость: 3 000 000 сум/год\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "❓ По вопросам: /complaint"
            )
        await update.message.reply_text(text, parse_mode="HTML")

    from telegram.ext import CommandHandler
    app.add_handler(CommandHandler("help", show_help))
    app.add_handler(MessageHandler(
        filters.Regex("^(📖 Справочник|📖 Qo'llanma)$"),
        show_help
    ))

    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt_photo), group=0)

    async def _text_guard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return
        if update.message.text in MENU_ALL:
            return
        if ctx.user_data.get("edit_field"):
            return
        if ctx.user_data.get("admin_mode"):
            return
        # Фильтр возраста — проверяем первым
        if await handle_age_filter_input(update, ctx):
            return
        await handle_city_input(update, ctx)

    # group=2 — ниже profile.py (group=1), чтобы редактирование профиля
    # обрабатывалось раньше чем city/age-filter поиска
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        _text_guard
    ), group=2)