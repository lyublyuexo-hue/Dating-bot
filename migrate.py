"""
Миграция БД: добавляет новые колонки и таблицы.
Запуск: python migrate.py
"""
import sqlite3
import os

# Укажи путь к своей БД если отличается
DB_PATH = os.path.join(os.path.dirname(__file__), "dating_bot.db")

# Попробуем найти БД автоматически если не там
if not os.path.exists(DB_PATH):
    for name in ("bot.db", "database.db", "db.sqlite3", "data.db", "dating.db"):
        candidate = os.path.join(os.path.dirname(__file__), name)
        if os.path.exists(candidate):
            DB_PATH = candidate
            break

print(f"Используем БД: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

migrations = [
    # Новые колонки в users
    ("ALTER TABLE users ADD COLUMN search_age_min INTEGER",          "users.search_age_min"),
    ("ALTER TABLE users ADD COLUMN search_age_max INTEGER",          "users.search_age_max"),

    # Таблица чёрного списка
    ("""
    CREATE TABLE IF NOT EXISTS blacklist (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(telegram_id),
        target_id  INTEGER NOT NULL REFERENCES users(telegram_id),
        created_at DATETIME DEFAULT (datetime('now'))
    )
    """, "table blacklist"),
]

for sql, label in migrations:
    try:
        cur.execute(sql)
        conn.commit()
        print(f"  ✅ {label}")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print(f"  ⏭  {label} — уже есть, пропускаем")
        else:
            print(f"  ❌ {label} — ошибка: {e}")

conn.close()
print("\nГотово! Перезапусти бота.")