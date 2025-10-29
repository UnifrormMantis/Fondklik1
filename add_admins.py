#!/usr/bin/env python3
"""Скрипт для добавления админов в FondKlik Bot"""

import sqlite3

DATABASE_PATH = "bot_database.db"

# ID админов
ADMIN_IDS = [739935417, 798427688]

def add_admins():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Создаем таблицу если её нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Добавляем админов
    for admin_id in ADMIN_IDS:
        cursor.execute('''
            INSERT OR IGNORE INTO admins (telegram_id)
            VALUES (?)
        ''', (admin_id,))
        print(f"✅ Админ {admin_id} добавлен")
    
    conn.commit()
    conn.close()
    print("\n🎉 Все админы добавлены!")

if __name__ == "__main__":
    add_admins()

