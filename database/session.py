"""
Единый движок БД для всего проекта.
Импортируй Session или get_session отсюда — не создавай новый engine в каждом файле.
"""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import settings

def _fix_db_url(url: str) -> str:
    """
    Railway даёт postgresql:// или postgres:// —
    SQLAlchemy async требует postgresql+asyncpg://
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

db_url = _fix_db_url(settings.DATABASE_URL)

engine = create_async_engine(
    db_url,
    echo=False,
    pool_pre_ping=True,
)

Session = async_sessionmaker(engine, expire_on_commit=False)

@asynccontextmanager
async def get_session() -> AsyncSession:
    async with Session() as session:
        yield session
