from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional
 
 
class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: str = "sqlite+aiosqlite:///dating_bot.db"
    ADMIN_IDS: List[int] = []
    ADMIN_GROUP_ID: Optional[int] = None
 
    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            v = v.strip()
            # JSON формат: [123, 456]
            if v.startswith("["):
                import json
                return json.loads(v)
            # Запятая-разделённый формат: 123,456
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v
 
    model_config = {
        "env_file": None,  # не читаем .env файл — берём только из переменных окружения
        "extra": "ignore",
    }
 
 
settings = Settings()
 
