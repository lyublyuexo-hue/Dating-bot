from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional

class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str = "sqlite+aiosqlite:///dating_bot.db"
    ADMIN_IDS: List[int] = []
    ADMIN_GROUP_ID: Optional[int] = None  # ← было GROUP_ID, исправлено

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    class Config:
        env_file = ".env"

settings = Settings()