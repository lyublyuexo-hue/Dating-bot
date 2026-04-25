"""
Скрипт миграции: добавляет таблицу vip_premium и колонку vip_contact_used в users.
Запуск: python3 migrate_vip.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "db.sqlite3")


def migrate():
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── 1. Колонка vip_contact_used в таблице users ───────────────────────
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [row[1] for row in cursor.fetchall()]

    if "vip_contact_used" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN vip_contact_used DATETIME")
        conn.commit()
        print("✅ Колонка vip_contact_used добавлена в таблицу users.")
    else:
        print("ℹ️  Колонка vip_contact_used уже существует.")

    # ── 2. Таблица vip_premium ────────────────────────────────────────────
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='vip_premium'
    """)
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE vip_premium (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    BIGINT  NOT NULL UNIQUE REFERENCES users(telegram_id),
                expires_at DATETIME NOT NULL,
                source     VARCHAR(32) DEFAULT 'purchase',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ Таблица vip_premium создана.")
    else:
        print("ℹ️  Таблица vip_premium уже существует.")

    conn.close()
    print("\n🎉 Миграция завершена!")


if __name__ == "__main__":
    migrate()