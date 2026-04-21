# Миграции (Alembic)

## Первый запуск

```bash
pip install alembic
alembic init migrations
```

В `alembic.ini` укажи:
```
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/dating_bot
```

В `migrations/env.py` подключи модели:
```python
from database.models import Base
target_metadata = Base.metadata
```

Создать миграцию:
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```
