#!/usr/bin/env python3
"""
Тест новой системы депозитов и рефералов
"""

import sqlite3
from datetime import datetime, timedelta

DATABASE_PATH = "bot_database.db"

def test_new_system():
    """Создать тестовые данные для новой системы"""
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Очищаем старые данные
        cursor.execute("DELETE FROM deposit_payments")
        cursor.execute("UPDATE users SET active_deposits_10 = 0, active_deposits_30 = 0")
        print("🗑️ Старые данные очищены")
        
        # Создаем тестовых пользователей
        test_users = [
            (739935417, "Dmitry", "Sulkovsky", "SulkovskyD", "TTest123456789012345678901234567890"),
            (123456789, "Alice", "Smith", "alice_smith", "TAlice123456789012345678901234567890"),
            (987654321, "Bob", "Johnson", "bob_johnson", "TBob123456789012345678901234567890"),
            (555666777, "Carol", "Brown", "carol_brown", "TCarol123456789012345678901234567890"),
            (111222333, "David", "Wilson", "david_wilson", "TDavid123456789012345678901234567890")
        ]
        
        print("👥 Создаем тестовых пользователей...")
        for user_id, first_name, last_name, username, wallet_address in test_users:
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (telegram_id, first_name, last_name, username, wallet_address, balance, total_earned, active_deposits_10, active_deposits_30)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, first_name, last_name, username, wallet_address, 0.0, 0.0, 0, 0))
        
        # Создаем админа
        cursor.execute('''
            INSERT OR REPLACE INTO admins (telegram_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (739935417, "SulkovskyD", "Dmitry", "Sulkovsky"))
        
        conn.commit()
        print("✅ Пользователи созданы")
        
        # Создаем депозиты разных типов
        print("\n💰 Создаем депозиты разных типов...")
        
        # Дмитрий - 30-дневный депозит
        print("📅 Дмитрий - 30-дневный депозит (100 USDT -> 130 USDT):")
        cursor.execute('UPDATE users SET active_deposits_30 = 1 WHERE telegram_id = 739935417')
        create_deposit_schedule(739935417, 100.0, '30_days', cursor)
        
        # Алиса - 10-дневный депозит
        print("📅 Алиса - 10-дневный депозит (50 USDT -> 54 USDT):")
        cursor.execute('UPDATE users SET active_deposits_10 = 1 WHERE telegram_id = 123456789')
        create_deposit_schedule(123456789, 50.0, '10_days', cursor)
        
        # Боб - оба типа депозитов
        print("📅 Боб - 30-дневный депозит (200 USDT -> 260 USDT):")
        cursor.execute('UPDATE users SET active_deposits_30 = 1 WHERE telegram_id = 987654321')
        create_deposit_schedule(987654321, 200.0, '30_days', cursor)
        
        print("📅 Боб - 10-дневный депозит (75 USDT -> 81 USDT):")
        cursor.execute('UPDATE users SET active_deposits_10 = 1 WHERE telegram_id = 987654321')
        create_deposit_schedule(987654321, 75.0, '10_days', cursor)
        
        # Кэрол - 10-дневный депозит
        print("📅 Кэрол - 10-дневный депозит (150 USDT -> 162 USDT):")
        cursor.execute('UPDATE users SET active_deposits_10 = 1 WHERE telegram_id = 555666777')
        create_deposit_schedule(555666777, 150.0, '10_days', cursor)
        
        # Дэвид - 30-дневный депозит
        print("📅 Дэвид - 30-дневный депозит (300 USDT -> 390 USDT):")
        cursor.execute('UPDATE users SET active_deposits_30 = 1 WHERE telegram_id = 111222333')
        create_deposit_schedule(111222333, 300.0, '30_days', cursor)
        
        conn.commit()
        print("\n✅ Все депозиты созданы")
        
        # Показываем статистику
        print(f"\n📊 СТАТИСТИКА:")
        cursor.execute('SELECT COUNT(*) FROM deposit_payments WHERE deposit_type = "10_days"')
        count_10 = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM deposit_payments WHERE deposit_type = "30_days"')
        count_30 = cursor.fetchone()[0]
        
        print(f"📅 10-дневных депозитов: {count_10} записей")
        print(f"📅 30-дневных депозитов: {count_30} записей")
        
        # Показываем активные депозиты
        cursor.execute('SELECT telegram_id, first_name, active_deposits_10, active_deposits_30 FROM users WHERE active_deposits_10 > 0 OR active_deposits_30 > 0')
        active_users = cursor.fetchall()
        
        print(f"\n👥 ПОЛЬЗОВАТЕЛИ С АКТИВНЫМИ ДЕПОЗИТАМИ:")
        for user_id, first_name, active_10, active_30 in active_users:
            print(f"   {first_name}: 10-дн: {active_10}, 30-дн: {active_30}")

def create_deposit_schedule(user_id, amount, deposit_type, cursor):
    """Создать расписание выплат для депозита"""
    
    # Получаем адрес кошелька
    wallet_result = cursor.execute('SELECT wallet_address FROM users WHERE telegram_id = ?', (user_id,)).fetchone()
    wallet_address = wallet_result[0] if wallet_result and wallet_result[0] else "Не указан"
    
    # Определяем параметры
    if deposit_type == '30_days':
        total_days = 30
        profit_percent = 0.30
    else:  # 10_days
        total_days = 10
        profit_percent = 0.08
    
    return_amount = amount * (1 + profit_percent)
    
    # Создаем записи для каждого дня
    for days_remaining in range(total_days, 0, -1):
        payment_date = datetime.now() + timedelta(days=days_remaining - 1)
        
        cursor.execute('''
            INSERT INTO deposit_payments 
            (user_id, original_amount, return_amount, payment_date, days_remaining, status, wallet_address, deposit_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, return_amount, payment_date.strftime('%Y-%m-%d'), days_remaining, 'pending', wallet_address, deposit_type))
    
    print(f"   Создано {total_days} записей: {amount} USDT -> {return_amount:.2f} USDT")

if __name__ == "__main__":
    test_new_system()
















