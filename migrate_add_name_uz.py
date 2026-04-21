"""
Скрипт миграции: добавляет колонку name_uz в таблицу tags.
Запуск: python3 migrate_add_name_uz.py
"""
import sqlite3
import os

# Укажи путь к своей БД
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "db.sqlite3")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Проверяем — вдруг колонка уже есть
    cursor.execute("PRAGMA table_info(tags)")
    columns = [row[1] for row in cursor.fetchall()]

    if "name_uz" in columns:
        print("✅ Колонка name_uz уже существует, миграция не нужна.")
        conn.close()
        return

    # Добавляем колонку
    cursor.execute("ALTER TABLE tags ADD COLUMN name_uz VARCHAR(64)")
    conn.commit()
    print("✅ Колонка name_uz успешно добавлена в таблицу tags.")

    conn.close()

if __name__ == "__main__":
    migrate()