from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, and_, or_, case, update, func
from sqlalchemy.orm import selectinload
from database.models import User, Like, ProfileView, Premium, VipPremium, Referral, BlackList
from database.session import Session

RESHOW_DAYS    = 7
LIMIT_FREE     = 20
LIMIT_REFERRAL = 30   # +10 за реферала
LIMIT_PREMIUM  = 70   # +50 за Premium
LIMIT_VIP      = 70   # VIP = те же 70 (бонус VIP — личка, не лимит)


class MatchService:

    @staticmethod
    async def _get_daily_limit(user_id: int, s) -> int:
        vip = (await s.execute(
            select(VipPremium).where(
                and_(VipPremium.user_id == user_id, VipPremium.expires_at > datetime.now())
            )
        )).scalar_one_or_none()
        if vip:
            return LIMIT_VIP

        prem = (await s.execute(
            select(Premium).where(
                and_(Premium.user_id == user_id, Premium.expires_at > datetime.now())
            )
        )).scalar_one_or_none()
        if prem:
            return LIMIT_PREMIUM

        ref_count = (await s.execute(
            select(func.count()).where(Referral.inviter_id == user_id)
        )).scalar()
        if ref_count > 0:
            return LIMIT_REFERRAL

        return LIMIT_FREE

    @staticmethod
    async def _get_views_today(user_id: int, s) -> int:
        """Считает уникальные профили просмотренные сегодня.
        Один профиль сколько бы раз не показывался — считается как 1."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return (await s.execute(
            select(func.count(func.distinct(ProfileView.target_id))).where(
                and_(ProfileView.viewer_id == user_id, ProfileView.viewed_at >= today)
            )
        )).scalar()

    @staticmethod
    async def get_daily_limit_info(user_id: int) -> dict:
        async with Session() as s:
            limit = await MatchService._get_daily_limit(user_id, s)
            used  = await MatchService._get_views_today(user_id, s)
            return {"limit": limit, "used": used, "left": max(0, limit - used)}

    @staticmethod
    async def _get_blacklisted_ids(user_id: int, s) -> set:
        """Возвращает ID пользователей, которых заблокировал user_id,
        И тех, кто заблокировал user_id (взаимное скрытие)."""
        blocked_by_me = {row[0] for row in (await s.execute(
            select(BlackList.target_id).where(BlackList.user_id == user_id)
        )).fetchall()}
        blocked_me = {row[0] for row in (await s.execute(
            select(BlackList.user_id).where(BlackList.target_id == user_id)
        )).fetchall()}
        return blocked_by_me | blocked_me

    @staticmethod
    async def get_next_profile(user_id: int):
        async with Session() as s:
            me = await s.get(User, user_id, options=[selectinload(User.tags)])
            if not me:
                return None

            limit = await MatchService._get_daily_limit(user_id, s)
            used  = await MatchService._get_views_today(user_id, s)
            if used >= limit:
                return "limit_reached"

            liked_ids = {row[0] for row in (await s.execute(
                select(Like.to_user_id).where(Like.from_user_id == user_id)
            )).fetchall()}

            blacklisted_ids = await MatchService._get_blacklisted_ids(user_id, s)

            cutoff = datetime.now() - timedelta(days=RESHOW_DAYS)
            recently_seen = {row[0] for row in (await s.execute(
                select(ProfileView.target_id).where(
                    and_(ProfileView.viewer_id == user_id, ProfileView.viewed_at > cutoff)
                )
            )).fetchall()}

            now   = datetime.now()
            boost = case((User.boost_until > now, 1), else_=0)

            def conditions(exclude):
                c = [
                    User.telegram_id != user_id,
                    User.is_active   == True,
                    User.ban_status  == "active",
                    User.photo_file_id.isnot(None),
                    User.age >= me.age_min,
                    User.age <= me.age_max,
                ]
                # Исключаем чёрный список всегда
                if blacklisted_ids:
                    c.append(User.telegram_id.notin_(blacklisted_ids))
                if exclude:
                    c.append(User.telegram_id.notin_(exclude))
                if me.looking_for != "all":
                    c.append(User.gender == me.looking_for)
                return c

            # Уровень 1: исключаем лайкнутых + недавно просмотренных
            profile = (await s.execute(
                select(User).options(selectinload(User.tags))
                .where(and_(*conditions(liked_ids | recently_seen)))
                .order_by(boost.desc(), User.activity_score.desc()).limit(1)
            )).scalar_one_or_none()

            # Уровень 2: сбрасываем историю просмотров, исключаем только лайкнутых
            if not profile:
                await s.execute(
                    update(ProfileView)
                    .where(ProfileView.viewer_id == user_id)
                    .values(viewed_at=datetime.now() - timedelta(days=RESHOW_DAYS + 1))
                )
                await s.commit()
                profile = (await s.execute(
                    select(User).options(selectinload(User.tags))
                    .where(and_(*conditions(liked_ids)))
                    .order_by(boost.desc(), User.activity_score.desc()).limit(1)
                )).scalar_one_or_none()

            # Уровень 3: показываем вообще всех (даже лайкнутых) — анкеты никогда не кончаются
            # При уровне 3 не записываем просмотр чтобы не накручивать лимит
            if not profile:
                profile = (await s.execute(
                    select(User).options(selectinload(User.tags))
                    .where(and_(*conditions(set())))
                    .order_by(boost.desc(), User.activity_score.desc()).limit(1)
                )).scalar_one_or_none()
                # Не записываем просмотр для уровня 3
                return profile

            if profile:
                await MatchService._record_view(s, user_id, profile.telegram_id)
            return profile

    @staticmethod
    async def _record_view(s, viewer_id: int, target_id: int):
        row = (await s.execute(
            select(ProfileView).where(
                and_(ProfileView.viewer_id == viewer_id, ProfileView.target_id == target_id)
            )
        )).scalar_one_or_none()
        if row:
            await s.execute(
                update(ProfileView)
                .where(and_(ProfileView.viewer_id == viewer_id, ProfileView.target_id == target_id))
                .values(viewed_at=datetime.now())
            )
        else:
            s.add(ProfileView(viewer_id=viewer_id, target_id=target_id))
        await s.commit()

    @staticmethod
    async def add_like(from_id: int, to_id: int) -> bool:
        """
        Возвращает True если матч, False если просто лайк.
        Возвращает None если уже лайкали (антиспам).
        """
        async with Session() as s:
            # Антиспам: проверяем, не лайкали ли уже
            existing = (await s.execute(
                select(Like).where(
                    and_(Like.from_user_id == from_id, Like.to_user_id == to_id)
                )
            )).scalar_one_or_none()
            if existing:
                return None  # уже лайкнут

            like = Like(from_user_id=from_id, to_user_id=to_id)
            s.add(like)
            reverse = (await s.execute(
                select(Like).where(and_(Like.from_user_id == to_id, Like.to_user_id == from_id))
            )).scalar_one_or_none()
            if reverse:
                like.is_match   = True
                reverse.is_match = True
                await s.commit()
                return True
            await s.commit()
            return False

    @staticmethod
    async def get_matches(user_id: int) -> List[Like]:
        async with Session() as s:
            return (await s.execute(
                select(Like).where(
                    and_(Like.is_match == True,
                         or_(Like.from_user_id == user_id, Like.to_user_id == user_id))
                )
            )).scalars().all()

    @staticmethod
    async def has_vip(user_id: int) -> bool:
        async with Session() as s:
            return (await s.execute(
                select(VipPremium).where(
                    and_(VipPremium.user_id == user_id, VipPremium.expires_at > datetime.now())
                )
            )).scalar_one_or_none() is not None

    @staticmethod
    async def can_use_vip_contact(user_id: int) -> bool:
        async with Session() as s:
            user = await s.get(User, user_id)
            if not user:
                return False
            if not user.vip_contact_used:
                return True
            return user.vip_contact_used < datetime.now() - timedelta(days=30)

    @staticmethod
    async def mark_vip_contact_used(user_id: int):
        async with Session() as s:
            user = await s.get(User, user_id)
            if user:
                user.vip_contact_used = datetime.now()
                await s.commit()

    # ══════════════════════════════════════════════════════
    # ЧЁРНЫЙ СПИСОК
    # ══════════════════════════════════════════════════════

    @staticmethod
    async def add_to_blacklist(user_id: int, target_id: int) -> bool:
        """Добавить в чёрный список. Возвращает False если уже есть."""
        async with Session() as s:
            existing = (await s.execute(
                select(BlackList).where(
                    and_(BlackList.user_id == user_id, BlackList.target_id == target_id)
                )
            )).scalar_one_or_none()
            if existing:
                return False
            s.add(BlackList(user_id=user_id, target_id=target_id))
            await s.commit()
            return True

    @staticmethod
    async def remove_from_blacklist(user_id: int, target_id: int) -> bool:
        async with Session() as s:
            row = (await s.execute(
                select(BlackList).where(
                    and_(BlackList.user_id == user_id, BlackList.target_id == target_id)
                )
            )).scalar_one_or_none()
            if not row:
                return False
            await s.delete(row)
            await s.commit()
            return True

    @staticmethod
    async def get_blacklist(user_id: int) -> List[BlackList]:
        async with Session() as s:
            return (await s.execute(
                select(BlackList).where(BlackList.user_id == user_id)
                .order_by(BlackList.created_at.desc())
            )).scalars().all()

    @staticmethod
    async def is_blacklisted(user_id: int, target_id: int) -> bool:
        async with Session() as s:
            row = (await s.execute(
                select(BlackList).where(
                    or_(
                        and_(BlackList.user_id == user_id, BlackList.target_id == target_id),
                        and_(BlackList.user_id == target_id, BlackList.target_id == user_id),
                    )
                )
            )).scalar_one_or_none()
            return row is not None

    # ══════════════════════════════════════════════════════
    # ПОИСК С ФИЛЬТРОМ ВОЗРАСТА (Premium)
    # ══════════════════════════════════════════════════════

    @staticmethod
    async def search_by_tag_filtered(
        user_id: int,
        tag_id: int,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        limit: int = 10
    ) -> List[User]:
        async with Session() as s:
            blacklisted = await MatchService._get_blacklisted_ids(user_id, s)
            conds = [
                User.is_active == True,
                User.ban_status == "active",
                User.telegram_id != user_id,
            ]
            from database.models import user_tags
            if age_min is not None:
                conds.append(User.age >= age_min)
            if age_max is not None:
                conds.append(User.age <= age_max)
            if blacklisted:
                conds.append(User.telegram_id.notin_(blacklisted))

            result = await s.execute(
                select(User)
                .join(user_tags, User.telegram_id == user_tags.c.user_id)
                .where(and_(user_tags.c.tag_id == tag_id, *conds))
                .limit(limit)
            )
            return result.scalars().all()

    @staticmethod
    async def search_by_city_filtered(
        user_id: int,
        city: str,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        limit: int = 10
    ) -> List[User]:
        async with Session() as s:
            blacklisted = await MatchService._get_blacklisted_ids(user_id, s)
            conds = [
                User.city.ilike(f"%{city}%"),
                User.is_active == True,
                User.ban_status == "active",
                User.telegram_id != user_id,
            ]
            if age_min is not None:
                conds.append(User.age >= age_min)
            if age_max is not None:
                conds.append(User.age <= age_max)
            if blacklisted:
                conds.append(User.telegram_id.notin_(blacklisted))

            result = await s.execute(
                select(User).where(and_(*conds)).limit(limit)
            )
            return result.scalars().all()

    @staticmethod
    async def save_search_age_filter(user_id: int, age_min: int, age_max: int):
        """Сохраняет фильтр возраста для поиска пользователя."""
        async with Session() as s:
            user = await s.get(User, user_id)
            if user:
                user.search_age_min = age_min
                user.search_age_max = age_max
                await s.commit()

    @staticmethod
    async def get_search_age_filter(user_id: int) -> tuple:
        """Возвращает (age_min, age_max) для поиска. None если не задан."""
        async with Session() as s:
            user = await s.get(User, user_id)
            if not user:
                return None, None
            return user.search_age_min, user.search_age_max
