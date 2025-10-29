#!/usr/bin/env python3
"""
Проверка админов в базе данных
"""

import sqlite3

DATABASE_PATH = "bot_database.db"

def check_admins():
    """Проверить админов в базе данных"""
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Проверяем админов
        cursor.execute('SELECT * FROM admins')
        admins = cursor.fetchall()
        
        print(f"📊 Админов в базе: {len(admins)}")
        
        if admins:
            print("👥 Список админов:")
            for admin in admins:
                print(f"   - ID: {admin[0]}, Username: {admin[1]}, Name: {admin[2]} {admin[3]}")
        else:
            print("❌ Нет админов в базе данных")
            
        # Проверяем пользователей
        cursor.execute('SELECT telegram_id, username, first_name FROM users LIMIT 5')
        users = cursor.fetchall()
        
        print(f"\n👤 Первые 5 пользователей:")
        for user in users:
            print(f"   - ID: {user[0]}, Username: {user[1]}, Name: {user[2]}")

if __name__ == "__main__":
    check_admins()

















