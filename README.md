# 🤖 Dating Bot — улучшенный аналог Дайвинчика

## Стек
- **python-telegram-bot 20+** (async)
- **PostgreSQL** + SQLAlchemy 2.0 (asyncpg)
- **Alembic** для миграций

## Запуск

```bash
# 1. Установи зависимости
pip install -r requirements.txt

# 2. Создай .env файл
cp .env.example .env
# Заполни BOT_TOKEN и DATABASE_URL

# 3. Запусти миграции
alembic upgrade head

# 4. Запусти бота
python main.py
```

## Структура
```
bot/
├── handlers/       — обработчики команд
├── modules/        — 5 ключевых модулей
│   ├── tags.py           — теги интересов
│   ├── verification.py   — верификация фото
│   ├── rating.py         — рейтинг активности
│   ├── moderation.py     — прозрачная модерация
│   └── mutual_interests.py — общие интересы при мэтче
├── services/       — бизнес-логика
└── keyboards/      — inline кнопки
database/
├── models.py       — SQLAlchemy модели
└── migrations/     — Alembic
```

## Ключевые улучшения над Дайвинчиком
| Функция | Дайвинчик | Этот бот |
|---|---|---|
| Теги интересов | ❌ | ✅ 14 тегов по категориям |
| Верификация фото | ❌ | ✅ Видео-кружок |
| Рейтинг активности | ❌ | ✅ Очки + приоритет показа |
| Причина бана | ❌ (теневой бан без объяснений) | ✅ Уведомление с причиной |
| Общие интересы | ❌ | ✅ Показ при мэтче |
