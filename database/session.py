"""
Единый движок БД для всего проекта.
Импортируй Session или get_session отсюда — не создавай новый engine в каждом файле.
"""
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

Session = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncSession:
    """Использование: async with get_session() as s: ..."""
    async with Session() as session:
        yield session