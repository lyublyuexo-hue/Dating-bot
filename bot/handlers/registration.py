"""
Регистрация нового пользователя.
Шаги: язык → имя → пол → возраст → город → фото → описание → кого ищу → теги
После регистрации — онбординг + реферал.
"""
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)
from sqlalchemy import select
from database.models import Referral, User
from database.session import Session
from bot.keyboards.main import (
    language_kb, gender_kb, looking_for_kb, tags_kb, main_menu_kb, home_inline_kb
)
from bot.services.user_service import UserService
from bot.modules.tags import TagModule
from bot.i18n import t

LANG, NAME, GENDER, AGE, CITY, PHOTO, ABOUT, LOOKING, TAGS = range(9)

BOOST_DAYS  = 7
BOOST_EVERY = 3


def _lang(ctx) -> str:
    return ctx.user_data.get("lang", "ru")


# ── Реферал ────────────────────────────────────────────────────────────────

async def _apply_referral(inviter_id: int, invitee_id: int):
    async with Session() as s:
        existing = await s.execute(
            select(Referral).where(Referral.invitee_id == invitee_id)
        )
        if existing.scalar_one_or_none():
            return 0

        s.add(Referral(inviter_id=inviter_id, invitee_id=invitee_id))
        await s.commit()

        count_result = await s.execute(
            select(Referral).where(Referral.inviter_id == inviter_id)
        )
        total = len(count_result.scalars().all())

        if total % BOOST_EVERY == 0:
            inviter = await s.get(User, inviter_id)
            if inviter:
                now = datetime.now()
                base = inviter.boost_until if inviter.boost_until and inviter.boost_until > now else now
                inviter.boost_until = base + timedelta(days=BOOST_DAYS)
                await s.commit()
            return total  # вернуть с бустом

        return total


# ── Старт ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args or []
    if args and args[0].startswith("ref_"):
        ctx.user_data["ref_code"] = args[0][4:]

    user = await UserService.get_user(update.effective_user.id)
    if user:
        # Уже зарегистрирован — показываем меню без /start
        lang = user.lang
        ctx.user_data["lang"] = lang
        await update.message.reply_text(
            t("home_text", lang),
            parse_mode="HTML",
            reply_markup=home_inline_kb(lang)
        )
        # Убираем команду /start из меню для этого пользователя
        await update.get_bot().set_my_commands(
            [
                ("language",  "🌐 Изменить язык / Til"),
                ("complaint", "✉️ Написать админу"),
            ]
        )
        return ConversationHandler.END

    # Новый пользователь
    await update.message.reply_text(
        t("reg_welcome", "ru"),
        parse_mode="HTML",
        reply_markup=language_kb()
    )
    return LANG
    # Новый пользователь — сначала выбор языка
    await update.message.reply_text(
        t("reg_welcome", "ru"),   # показываем двуязычное приветствие
        parse_mode="HTML",
        reply_markup=language_kb()
    )
    return LANG


# ── Шаг 0: Язык ─────────────────────────────────────────────────────────────

async def get_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split(":")[1]
    ctx.user_data["lang"] = lang
    await query.message.reply_text(t("reg_ask_name", lang))
    return NAME


# ── Шаг 1: Имя ──────────────────────────────────────────────────────────────

async def get_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = _lang(ctx)
    ctx.user_data["name"] = update.message.text.strip()[:64]
    await update.message.reply_text(
        t("reg_ask_gender", lang, name=ctx.user_data["name"]),
        reply_markup=gender_kb(lang)
    )
    return GENDER


# ── Шаг 2: Пол ──────────────────────────────────────────────────────────────

async def get_gender(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = _lang(ctx)
    ctx.user_data["gender"] = query.data.split(":")[1]
    await query.message.reply_text(t("reg_ask_age", lang))
    return AGE


# ── Шаг 3: Возраст ──────────────────────────────────────────────────────────

async def get_age(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = _lang(ctx)
    try:
        age = int(update.message.text.strip())
        if not 14 <= age <= 100:
            raise ValueError
    except ValueError:
        await update.message.reply_text(t("reg_age_error", lang))
        return AGE
    ctx.user_data["age"] = age
    await update.message.reply_text(t("reg_ask_city", lang))
    return CITY


# ── Шаг 4: Город ────────────────────────────────────────────────────────────

async def get_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = _lang(ctx)
    ctx.user_data["city"] = update.message.text.strip()[:64]
    await update.message.reply_text(t("reg_ask_photo", lang))
    return PHOTO


# ── Шаг 5: Фото ─────────────────────────────────────────────────────────────

async def get_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = _lang(ctx)
    if not update.message.photo:
        await update.message.reply_text(t("reg_photo_error", lang))
        return PHOTO
    ctx.user_data["photo_file_id"] = update.message.photo[-1].file_id
    await update.message.reply_text(t("reg_ask_about", lang))
    return ABOUT


# ── Шаг 6: О себе ───────────────────────────────────────────────────────────

async def get_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = _lang(ctx)
    text = update.message.text.strip()
    ctx.user_data["about"] = None if text == "-" else text[:500]
    await update.message.reply_text(t("reg_ask_looking", lang), reply_markup=looking_for_kb(lang))
    return LOOKING


# ── Шаг 7: Кого ищу ─────────────────────────────────────────────────────────

async def get_looking(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = _lang(ctx)
    ctx.user_data["looking_for"] = query.data.split(":")[1]
    all_tags = await TagModule.get_all_tags()
    ctx.user_data["selected_tags"] = set()
    await query.message.reply_text(
        t("reg_ask_tags", lang),
        reply_markup=tags_kb(all_tags, set(), lang)
    )
    return TAGS


# ── Шаг 8: Теги — переключение ───────────────────────────────────────────────

async def toggle_tag(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = _lang(ctx)
    tag_id = int(query.data.split(":")[1])
    selected = ctx.user_data.setdefault("selected_tags", set())
    if tag_id in selected:
        selected.discard(tag_id)
    else:
        selected.add(tag_id)
    all_tags = await TagModule.get_all_tags()
    await query.edit_message_reply_markup(reply_markup=tags_kb(all_tags, selected, lang))
    return TAGS


# ── Шаг 8: Теги — готово / создание профиля ──────────────────────────────────
async def finish_tags(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = _lang(ctx)
    data = ctx.user_data

    user = await UserService.create_user(
        telegram_id=update.effective_user.id,
        username=update.effective_user.username,
        name=data["name"],
        gender=data["gender"],
        age=data["age"],
        city=data["city"],
        photo_file_id=data["photo_file_id"],
        about=data.get("about"),
        looking_for=data["looking_for"],
        tag_ids=list(data.get("selected_tags", [])),
        lang=lang,
    )

    ctx.user_data["lang"] = lang  # ← сохраняем язык

    await query.message.reply_text(
        t("reg_done", lang, name=user.name),
        reply_markup=main_menu_kb(lang)
    )
    await query.message.reply_text(t("onboarding_1", lang), parse_mode="HTML")
    await query.message.reply_text(t("onboarding_2", lang), parse_mode="HTML")

    # Реферал
    ref_code = data.get("ref_code")
    if ref_code:
        async with Session() as s:
            from sqlalchemy import select as sa_select
            result = await s.execute(
                sa_select(User).where(User.referral_code == ref_code)
            )
            inviter = result.scalar_one_or_none()

        if inviter and inviter.telegram_id != user.telegram_id:
            total = await _apply_referral(inviter.telegram_id, user.telegram_id)
            boost_msg = ""
            if total and total % BOOST_EVERY == 0:
                inviter_lang = inviter.lang or "ru"
                boost_msg = t("referral_boost_earned", inviter_lang, days=BOOST_DAYS)
            try:
                inviter_lang = inviter.lang or "ru"
                await query.get_bot().send_message(
                    inviter.telegram_id,
                    t("referral_invited", inviter_lang, count=total, boost=boost_msg),
                    parse_mode="HTML"
                )
            except Exception:
                pass

    # Убираем /start из команд после регистрации
    try:
        await query.get_bot().set_my_commands([
            ("language",  "🌐 Изменить язык / Til"),
            ("complaint", "✉️ Написать админу"),
        ])
    except Exception:
        pass

    return ConversationHandler.END
# ── Отмена ───────────────────────────────────────────────────────────────────

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = _lang(ctx)
    await update.message.reply_text(t("reg_cancelled", lang))
    return ConversationHandler.END


# ── Регистрация хендлеров ─────────────────────────────────────────────────────
from telegram.ext import MessageHandler, filters

async def _menu_fallback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Если пользователь нажал кнопку меню во время регистрации — выходим из диалога."""
    return ConversationHandler.END


def register_handlers(app: Application):
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            LANG: [CallbackQueryHandler(get_lang, pattern="^lang:")],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER: [CallbackQueryHandler(get_gender, pattern="^gender:")],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_about)],
            LOOKING: [CallbackQueryHandler(get_looking, pattern="^looking:")],
            TAGS: [
                CallbackQueryHandler(finish_tags, pattern="^tags:done$"),
                CallbackQueryHandler(toggle_tag,  pattern="^tag:"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start",  cmd_start),
            # Все кнопки меню выбрасывают из диалога регистрации
            MessageHandler(
                filters.Regex(
                    "^(👀 Смотреть анкеты|👀 Anketalarni ko'rish"
                    "|🔍 Поиск|🔍 Qidiruv"
                    "|⭐ Избранные|⭐ Sevimlilar"
                    "|🔗 Реферал|🔗 Referal"
                    "|👤 Мой профиль|👤 Mening anketam)$"
                ),
                _menu_fallback
            ),
        ],
        allow_reentry=True,
        per_message=False,
    )
    app.add_handler(conv)