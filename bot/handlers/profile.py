from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)
from bot.services.user_service import UserService
from bot.keyboards.main import (
    profile_actions_kb, profile_edit_kb, profile_delete_confirm_kb,
    looking_for_kb, tags_kb
)
from bot.i18n import t
from bot.modules.tags import TagModule

MENU_BUTTONS = {
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


def _profile_text(user, lang: str) -> str:
    ver_map = {
        "none":     "",
        "pending":  t("ver_pending",  lang),
        "verified": t("ver_verified", lang),
        "rejected": t("ver_rejected", lang),
    }
    verified  = ver_map.get(user.verification_status, "")
    tags_text = ", ".join(
        f"{tag.emoji or ''}{tag.name_uz if lang == 'uz' and tag.name_uz else tag.name}"
        for tag in user.tags
    ) or t("profile_no_tags", lang)

    return t("profile_caption", lang,
             name=user.name,
             age=user.age,
             city=user.city,
             verified=verified,
             score=user.activity_score,
             about=user.about or t("profile_no_about", lang),
             tags=tags_text)


async def show_profile(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        message = update.callback_query.message
        user_id = update.callback_query.from_user.id
    else:
        message = update.message
        user_id = update.effective_user.id

    lang = await _get_lang(user_id, ctx)
    user = await UserService.get_user(user_id)
    if not user:
        await message.reply_text(t("profile_not_found", lang))
        return

    text = _profile_text(user, lang)
    if not user.is_active:
        text += f"\n\n{t('profile_hidden_by_user', lang)}"

    kb = profile_actions_kb(lang, is_active=user.is_active)
    if user.photo_file_id:
        await message.reply_photo(
            photo=user.photo_file_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb
        )
    else:
        await message.reply_text(text, parse_mode="HTML", reply_markup=kb)


async def handle_profile_action(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    action  = query.data.split(":")[1]
    lang    = await _get_lang(update.effective_user.id, ctx)
    user_id = update.effective_user.id

    if action == "edit":
        await query.message.reply_text(
            t("profile_edit_choose", lang),
            reply_markup=profile_edit_kb(lang)
        )

    elif action == "photo":
        ctx.user_data["edit_field"] = "photo"
        await query.message.reply_text(t("edit_ask_photo", lang))

    elif action == "preview":
        user = await UserService.get_user(user_id)
        from bot.keyboards.main import like_skip_kb
        text = _profile_text(user, lang)
        if user.photo_file_id:
            await query.message.reply_photo(
                photo=user.photo_file_id,
                caption=text,
                parse_mode="HTML",
                reply_markup=like_skip_kb(user_id, lang)
            )
        else:
            await query.message.reply_text(text, parse_mode="HTML")

    elif action == "toggle":
        user      = await UserService.get_user(user_id)
        new_state = not user.is_active
        await UserService.update_user(user_id, is_active=new_state)
        await show_profile(update, ctx)

    elif action == "delete":
        await query.message.reply_text(
            t("profile_delete_confirm", lang),
            reply_markup=profile_delete_confirm_kb(lang)
        )

    elif action == "delete_confirm":
        await UserService.delete_user(user_id)
        ctx.user_data.clear()
        await query.message.reply_text(t("profile_deleted", lang))

    elif action == "back":
        await show_profile(update, ctx)


async def handle_edit_choice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    lang   = await _get_lang(update.effective_user.id, ctx)
    field  = query.data.split(":")[1]
    ctx.user_data["edit_field"] = field

    if field == "tags":
        all_tags = await TagModule.get_all_tags()
        user     = await UserService.get_user(update.effective_user.id)
        selected = {tag.id for tag in user.tags}
        ctx.user_data["selected_tags"] = selected
        await query.message.reply_text(
            t("reg_ask_tags", lang),
            reply_markup=tags_kb(all_tags, selected, lang)
        )
    elif field == "looking":
        await query.message.reply_text(
            t("edit_ask_looking", lang),
            reply_markup=looking_for_kb(lang)
        )
    else:
        ask_map = {
            "name":  "edit_ask_name",
            "age":   "edit_ask_age",
            "city":  "edit_ask_city",
            "about": "edit_ask_about",
        }
        if field in ask_map:
            await query.message.reply_text(t(ask_map[field], lang))


async def handle_edit_looking(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    lang   = await _get_lang(update.effective_user.id, ctx)
    if ctx.user_data.get("edit_field") != "looking":
        return
    value = query.data.split(":")[1]
    await UserService.update_user(update.effective_user.id, looking_for=value)
    ctx.user_data.pop("edit_field", None)
    await query.message.reply_text(t("edit_saved", lang))
    await show_profile(update, ctx)


async def handle_edit_tag_toggle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    lang   = await _get_lang(update.effective_user.id, ctx)
    if ctx.user_data.get("edit_field") != "tags":
        return
    tag_id   = int(query.data.split(":")[1])
    selected = ctx.user_data.setdefault("selected_tags", set())
    if tag_id in selected:
        selected.discard(tag_id)
    else:
        selected.add(tag_id)
    all_tags = await TagModule.get_all_tags()
    await query.edit_message_reply_markup(reply_markup=tags_kb(all_tags, selected, lang))


async def handle_edit_tags_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    lang   = await _get_lang(update.effective_user.id, ctx)
    if ctx.user_data.get("edit_field") != "tags":
        return

    selected = list(ctx.user_data.get("selected_tags", set()))

    from database.models import User, Tag
    from database.session import Session
    from sqlalchemy import select
    async with Session() as s:
        db_user = await s.get(User, update.effective_user.id)
        result  = await s.execute(select(Tag).where(Tag.id.in_(selected)))
        db_user.tags = result.scalars().all()
        await s.commit()

    ctx.user_data.pop("edit_field",    None)
    ctx.user_data.pop("selected_tags", None)
    await query.message.reply_text(t("edit_saved", lang))
    await show_profile(update, ctx)


async def handle_edit_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    field = ctx.user_data.get("edit_field")
    if not field or field in ("tags", "looking"):
        return
    lang    = await _get_lang(update.effective_user.id, ctx)
    user_id = update.effective_user.id

    if field == "photo":
        if not update.message.photo:
            await update.message.reply_text(t("reg_photo_error", lang))
            return
        await UserService.update_user(user_id, photo_file_id=update.message.photo[-1].file_id)
        ctx.user_data.pop("edit_field", None)
        await update.message.reply_text(t("edit_saved", lang))
        await show_profile(update, ctx)
        return

    text = update.message.text.strip()

    # Если пользователь нажал кнопку меню пока был в режиме редактирования —
    # сбрасываем edit_field и не сохраняем
    if text in MENU_BUTTONS:
        ctx.user_data.pop("edit_field", None)
        return

    if field == "age":
        try:
            age = int(text)
            if not 14 <= age <= 100:
                raise ValueError
        except ValueError:
            await update.message.reply_text(t("edit_age_error", lang))
            return
        await UserService.update_user(user_id, age=age)
    elif field == "name":
        await UserService.update_user(user_id, name=text[:64])
    elif field == "city":
        await UserService.update_user(user_id, city=text[:64])
    elif field == "about":
        await UserService.update_user(user_id, about=None if text == "-" else text[:500])

    ctx.user_data.pop("edit_field", None)
    await update.message.reply_text(t("edit_saved", lang))
    await show_profile(update, ctx)


def register_handlers(app: Application):
    app.add_handler(MessageHandler(
        filters.Regex("^(👤 Мой профиль|👤 Mening anketam)$"),
        show_profile
    ))

    app.add_handler(CallbackQueryHandler(handle_profile_action,  pattern="^profile:"))
    app.add_handler(CallbackQueryHandler(handle_edit_choice,     pattern="^edit:"))
    app.add_handler(CallbackQueryHandler(handle_edit_tag_toggle, pattern="^tag:"))
    app.add_handler(CallbackQueryHandler(handle_edit_tags_done,  pattern="^tags:done$"))
    app.add_handler(CallbackQueryHandler(handle_edit_looking,    pattern="^looking:"))

    # Группа 1 — выше приоритетом чем home.py (group=2)
    # Срабатывает ТОЛЬКО когда edit_field активен
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_text),
        group=1
    )
    app.add_handler(
        MessageHandler(filters.PHOTO, handle_edit_text),
        group=1
    )