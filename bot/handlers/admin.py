import asyncio
import logging
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.error import Forbidden
from sqlalchemy import select, func

from database.session import get_session
from database.models import User, Like, Premium, Referral
from bot.services.moderation_service import ModerationService
from bot.services.user_service import UserService
from config import settings

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


def admin_main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика",  callback_data="adm:stats")],
        [InlineKeyboardButton("📈 Dashboard",   callback_data="adm:dashboard")],
        [InlineKeyboardButton("👑 Premium",      callback_data="adm:give_premium"),
         InlineKeyboardButton("⛔ Бан",          callback_data="adm:ban")],
        [InlineKeyboardButton("📢 Рассылка",    callback_data="adm:broadcast")],
        [InlineKeyboardButton("🔎 Поиск",       callback_data="adm:search")],
        [InlineKeyboardButton("🚨 Жалобы",      callback_data="adm:reports")],
        [InlineKeyboardButton("🚪 Выйти",       callback_data="adm:exit")],
    ])


async def notify_group(bot: Bot, text: str, photo=None) -> None:
    if not settings.ADMIN_GROUP_ID:
        return
    try:
        if photo:
            await bot.send_photo(
                chat_id=settings.ADMIN_GROUP_ID,
                photo=photo,
                caption=text,
                parse_mode="HTML"
            )
        else:
            await bot.send_message(
                chat_id=settings.ADMIN_GROUP_ID,
                text=text,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"notify_group error: {e}")


async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    ctx.user_data["admin_mode"] = True
    await update.message.reply_text(
        "🛠 <b>Админ-панель</b>",
        parse_mode="HTML",
        reply_markup=admin_main_kb()
    )


async def handle_admin_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        return
    if not ctx.user_data.get("admin_mode"):
        return

    action = query.data.split(":")[1]

    if action == "stats":
        await show_stats(query)
    elif action == "dashboard":
        await show_dashboard(query)
    elif action == "give_premium":
        ctx.user_data["adm_state"] = "premium"
        await query.message.reply_text(
            "Введи ID и количество дней через пробел:\n<code>123456789 30</code>",
            parse_mode="HTML"
        )
    elif action == "ban":
        ctx.user_data["adm_state"] = "ban"
        await query.message.reply_text(
            "Введи команду:\n<code>ban 123456789</code> или <code>unban 123456789</code>",
            parse_mode="HTML"
        )
    elif action == "broadcast":
        ctx.user_data["adm_state"] = "broadcast"
        await query.message.reply_text("Отправь текст рассылки:")
    elif action == "search":
        ctx.user_data["adm_state"] = "search"
        await query.message.reply_text("Введи ID пользователя:")
    elif action == "reports":
        await show_reports(query)
    elif action == "exit":
        ctx.user_data.clear()
        await query.message.edit_text("🚪 Вышли из админки")


async def show_stats(query):
    async with get_session() as s:
        total_users  = (await s.execute(select(func.count()).select_from(User))).scalar()
        active_users = (await s.execute(select(func.count()).where(User.is_active == True))).scalar()
        banned_users = (await s.execute(select(func.count()).where(User.ban_status != "active"))).scalar()
        total_likes  = (await s.execute(select(func.count()).select_from(Like))).scalar()
        total_matches = (await s.execute(select(func.count()).where(Like.is_match == True))).scalar()
        total_premium = (await s.execute(
            select(func.count()).where(Premium.expires_at > datetime.now())
        )).scalar()
        today     = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        new_today = (await s.execute(select(func.count()).where(User.created_at >= today))).scalar()
        week_ago  = datetime.now() - timedelta(days=7)
        new_week  = (await s.execute(select(func.count()).where(User.created_at >= week_ago))).scalar()

    await query.message.reply_text(
        "📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"✅ Активные: <b>{active_users}</b>\n"
        f"⛔ Забанены: <b>{banned_users}</b>\n\n"
        f"📅 Новых сегодня: <b>{new_today}</b>\n"
        f"📆 За 7 дней: <b>{new_week}</b>\n\n"
        f"❤️ Лайков: <b>{total_likes}</b>\n"
        f"💘 Мэтчей: <b>{total_matches}</b>\n\n"
        f"⭐ Premium активных: <b>{total_premium}</b>",
        parse_mode="HTML"
    )


async def show_dashboard(query):
    async with get_session() as s:
        top_users = (await s.execute(
            select(User.telegram_id, User.name, func.count(Like.id).label("likes"))
            .join(Like, Like.from_user_id == User.telegram_id)
            .group_by(User.telegram_id)
            .order_by(func.count(Like.id).desc())
            .limit(5)
        )).fetchall()

        top_refs = (await s.execute(
            select(Referral.inviter_id, func.count().label("count"))
            .group_by(Referral.inviter_id)
            .order_by(func.count().desc())
            .limit(5)
        )).fetchall()

    text = "📈 <b>Dashboard</b>\n\n🔥 Топ по лайкам:\n"
    for row in top_users:
        text += f"• {row.name} — {row.likes} лайков\n"

    text += "\n🔗 Топ рефералов:\n"
    for row in top_refs:
        text += f"• <code>{row.inviter_id}</code> — {row.count} чел.\n"

    await query.message.reply_text(text, parse_mode="HTML")


async def give_premium(user_id: int, days: int) -> bool:
    async with get_session() as s:
        user = await s.get(User, user_id)
        if not user:
            return False
        expires = datetime.now() + timedelta(days=days)
        s.add(Premium(user_id=user_id, expires_at=expires))
        await s.commit()
        return True


async def show_reports(query):
    reports = await ModerationService.get_pending_reports()
    if not reports:
        await query.message.reply_text("✅ Жалоб нет")
        return
    for r in reports[:5]:
        await query.message.reply_text(
            f"🚨 Жалоба #{r.id}\n"
            f"На пользователя: <code>{r.target_id}</code>\n"
            f"Причина: {r.reason}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "✅ Закрыть",
                    callback_data=f"adm_resolve:{r.id}"
                )
            ]])
        )


async def handle_admin_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not ctx.user_data.get("admin_mode"):
        return

    state = ctx.user_data.get("adm_state")
    if not state:
        return

    text = update.message.text.strip()

    if state == "premium":
        try:
            parts   = text.split()
            user_id = int(parts[0])
            days    = int(parts[1])
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Формат: <code>123456789 30</code>", parse_mode="HTML")
            return
        ok = await give_premium(user_id, days)
        if ok:
            await update.message.reply_text(f"✅ Premium выдан на {days} дней")
            try:
                await ctx.bot.send_message(
                    user_id,
                    f"🎉 Вам выдан <b>Premium на {days} дней</b>! ⭐",
                    parse_mode="HTML"
                )
            except Exception:
                pass
        else:
            await update.message.reply_text("❌ Пользователь не найден")
        ctx.user_data.pop("adm_state", None)

    elif state == "ban":
        try:
            parts  = text.split()
            action = parts[0].lower()
            uid    = int(parts[1])
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ Формат: <code>ban 123456789</code>",
                parse_mode="HTML"
            )
            return
        if action == "ban":
            await ModerationService.ban_user(uid, "admin ban")
            await update.message.reply_text(f"⛔ Пользователь <code>{uid}</code> забанен", parse_mode="HTML")
        elif action == "unban":
            await ModerationService.unban_user(uid)
            await update.message.reply_text(f"✅ Пользователь <code>{uid}</code> разбанен", parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Команда: ban или unban")
        ctx.user_data.pop("adm_state", None)

    elif state == "search":
        ctx.user_data.pop("adm_state", None)
        try:
            uid  = int(text)
            user = await UserService.get_user(uid)
        except ValueError:
            await update.message.reply_text("❌ Введи числовой ID")
            return
        if not user:
            await update.message.reply_text("❌ Пользователь не найден")
            return
        await update.message.reply_text(
            f"👤 <b>{user.name}</b>, {user.age} — {user.city}\n"
            f"ID: <code>{user.telegram_id}</code>\n"
            f"Статус: {user.ban_status}\n"
            f"Активен: {'да' if user.is_active else 'нет'}",
            parse_mode="HTML"
        )

    elif state == "broadcast":
        ctx.user_data.pop("adm_state", None)
        async with get_session() as s:
            result = await s.execute(select(User.telegram_id).where(User.is_active == True))
            ids    = [row[0] for row in result.fetchall()]
        sent = 0
        for uid in ids:
            try:
                await ctx.bot.send_message(uid, text)
                sent += 1
                await asyncio.sleep(0.05)
            except Forbidden:
                await UserService.update_user(uid, is_active=False)
            except Exception:
                pass
        await update.message.reply_text(f"✅ Отправлено: {sent} из {len(ids)}")


async def handle_resolve_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(update.effective_user.id):
        return
    report_id = int(query.data.split(":")[1])
    await ModerationService.resolve_report(report_id)
    await query.message.edit_text("✅ Жалоба закрыта")


def register_handlers(app: Application):
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(handle_admin_menu,     pattern="^adm:"))
    app.add_handler(CallbackQueryHandler(handle_resolve_report, pattern="^adm_resolve:"))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(user_id=settings.ADMIN_IDS),
        handle_admin_input
    ))