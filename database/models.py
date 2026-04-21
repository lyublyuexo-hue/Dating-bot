from sqlalchemy import (
    Column, BigInteger, String, Integer, Boolean, DateTime,
    Text, ForeignKey, Table, func
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


user_tags = Table(
    "user_tags", Base.metadata,
    Column("user_id", BigInteger, ForeignKey("users.telegram_id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    telegram_id   = Column(BigInteger, primary_key=True)
    username      = Column(String(64),  nullable=True)
    name          = Column(String(64),  nullable=False)
    age           = Column(Integer,     nullable=False)
    gender        = Column(String(16),  nullable=False)
    city          = Column(String(64),  nullable=False)
    about         = Column(Text,        nullable=True)
    photo_file_id = Column(String(256), nullable=True)

    looking_for   = Column(String(16), default="all")
    age_min       = Column(Integer,    default=14)
    age_max       = Column(Integer,    default=99)

    # Язык интерфейса — хранится в БД, не теряется при рестарте
    lang          = Column(String(4), default="ru", nullable=False)

    verification_status = Column(String(16), default="none")
    activity_score      = Column(Integer,    default=0)
    ban_status          = Column(String(16), default="active")
    ban_reason          = Column(Text,       nullable=True)

    is_active     = Column(Boolean,  default=True)
    created_at    = Column(DateTime, server_default=func.now())
    last_seen     = Column(DateTime, server_default=func.now(), onupdate=func.now())

    boost_until   = Column(DateTime, nullable=True)
    referral_code = Column(String(32), unique=True, nullable=True)

    tags           = relationship("Tag",      secondary=user_tags, back_populates="users")
    likes_sent     = relationship("Like",     foreign_keys="Like.from_user_id", back_populates="from_user")
    likes_received = relationship("Like",     foreign_keys="Like.to_user_id",   back_populates="to_user")
    reports_sent   = relationship("Report",   foreign_keys="Report.reporter_id", back_populates="reporter")
    premium        = relationship("Premium",  back_populates="user", uselist=False)
    favorites_sent = relationship("Favorite", foreign_keys="Favorite.user_id",   back_populates="user")
    referrals_sent = relationship("Referral", foreign_keys="Referral.inviter_id", back_populates="inviter")


class Tag(Base):
    __tablename__ = "tags"

    id       = Column(Integer,    primary_key=True, autoincrement=True)
    name     = Column(String(64), unique=True, nullable=False)
    name_uz  = Column(String(64), nullable=True)   # узбекский вариант названия
    emoji    = Column(String(8),  nullable=True)
    category = Column(String(32), nullable=True)

    users = relationship("User", secondary=user_tags, back_populates="tags")


class Like(Base):
    __tablename__ = "likes"

    id           = Column(Integer,   primary_key=True, autoincrement=True)
    from_user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    to_user_id   = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    is_match     = Column(Boolean, default=False)
    created_at   = Column(DateTime, server_default=func.now())

    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="likes_sent")
    to_user   = relationship("User", foreign_keys=[to_user_id],   back_populates="likes_received")


class Report(Base):
    __tablename__ = "reports"

    id          = Column(Integer,   primary_key=True, autoincrement=True)
    reporter_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    target_id   = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    reason      = Column(String(128), nullable=False)
    comment     = Column(Text,        nullable=True)
    resolved    = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())

    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports_sent")


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id         = Column(Integer,   primary_key=True, autoincrement=True)
    user_id    = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    action     = Column(String(64), nullable=False)
    points     = Column(Integer,   default=0)
    created_at = Column(DateTime,  server_default=func.now())


class Premium(Base):
    __tablename__ = "premium"

    id         = Column(Integer,   primary_key=True, autoincrement=True)
    user_id    = Column(BigInteger, ForeignKey("users.telegram_id"), unique=True, nullable=False)
    expires_at = Column(DateTime,  nullable=False)
    source     = Column(String(32), default="purchase")
    created_at = Column(DateTime,  server_default=func.now())

    user = relationship("User", back_populates="premium")


class Favorite(Base):
    __tablename__ = "favorites"

    id         = Column(Integer,   primary_key=True, autoincrement=True)
    user_id    = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    target_id  = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    created_at = Column(DateTime,  server_default=func.now())

    user   = relationship("User", foreign_keys=[user_id],  back_populates="favorites_sent")
    target = relationship("User", foreign_keys=[target_id])


class Referral(Base):
    __tablename__ = "referrals"

    id         = Column(Integer,   primary_key=True, autoincrement=True)
    inviter_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    invitee_id = Column(BigInteger, ForeignKey("users.telegram_id"), unique=True, nullable=False)
    created_at = Column(DateTime,  server_default=func.now())

    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="referrals_sent")
    invitee = relationship("User", foreign_keys=[invitee_id])


async def init_db():
    from database.session import engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)