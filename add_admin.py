#!/usr/bin/env python3
"""
Скрипт для добавления администратора
"""

import sqlite3
import sys

DATABASE_PATH = "bot_database.db"

def add_admin(user_id):
    """Добавить пользователя в админы"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Проверяем существует ли пользователь
        cursor.execute("SELECT telegram_id, username FROM users WHERE telegram_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ Пользователь {user_id} не найден в базе данных")
            print(f"💡 Попросите пользователя написать /start боту сначала")
            conn.close()
            return False
        
        # Обновляем статус админа
        cursor.execute("UPDATE users SET is_admin = 1 WHERE telegram_id = ?", (user_id,))
        conn.commit()
        
        username = user[1] if user[1] else "без username"
        print(f"✅ Пользователь {user_id} ({username}) теперь администратор!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def list_admins():
    """Показать всех админов"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT telegram_id, username, first_name, last_name 
            FROM users 
            WHERE is_admin = 1
        """)
        
        admins = cursor.fetchall()
        
        if not admins:
            print("📝 Админов пока нет")
        else:
            print(f"👥 Всего админов: {len(admins)}")
            print()
            for admin in admins:
                telegram_id, username, first_name, last_name = admin
                name = f"{first_name or ''} {last_name or ''}".strip() or "Без имени"
                username_str = f"@{username}" if username else "без username"
                print(f"  • {telegram_id} - {name} ({username_str})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def list_all_users():
    """Показать всех пользователей"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT telegram_id, username, first_name, last_name, is_admin 
            FROM users 
            ORDER BY is_admin DESC, telegram_id ASC
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("📝 Пользователей пока нет")
        else:
            print(f"👥 Всего пользователей: {len(users)}")
            print()
            for user in users:
                telegram_id, username, first_name, last_name, is_admin = user
                name = f"{first_name or ''} {last_name or ''}".strip() or "Без имени"
                username_str = f"@{username}" if username else "без username"
                admin_badge = "⭐ АДМИН" if is_admin else ""
                print(f"  • {telegram_id} - {name} ({username_str}) {admin_badge}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🔧 УПРАВЛЕНИЕ АДМИНИСТРАТОРАМИ")
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            list_admins()
        elif command == "users":
            list_all_users()
        elif command == "add" and len(sys.argv) > 2:
            try:
                user_id = int(sys.argv[2])
                add_admin(user_id)
            except ValueError:
                print("❌ User ID должен быть числом")
        else:
            print("Использование:")
            print("  python3 add_admin.py list        - показать всех админов")
            print("  python3 add_admin.py users       - показать всех пользователей")
            print("  python3 add_admin.py add USER_ID - добавить админа")
    else:
        print("Доступные команды:")
        print()
        print("1. Показать всех админов:")
        print("   python3 add_admin.py list")
        print()
        print("2. Показать всех пользователей:")
        print("   python3 add_admin.py users")
        print()
        print("3. Добавить админа:")
        print("   python3 add_admin.py add YOUR_USER_ID")
        print()
        print("💡 Как узнать свой USER_ID:")
        print("   1. Напишите боту /start")
        print("   2. Используйте @userinfobot в Telegram")
        print()
        
        # Показываем текущих пользователей
        print("=" * 50)
        print()
        list_all_users()

