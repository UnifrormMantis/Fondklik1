#!/usr/bin/env python3
"""
Создание тестовых данных с разным количеством выплат в разные дни
"""

import sqlite3
from datetime import datetime, timedelta

DATABASE_PATH = "bot_database.db"

def create_varied_deposits():
    """Создать тестовые данные с разным количеством выплат"""
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Очищаем старые данные
        cursor.execute("DELETE FROM deposit_payments")
        print("🗑️ Старые данные очищены")
        
        # Создаем тестовых пользователей
        test_users = [
            (739935417, "Dmitry", "Sulkovsky", "SulkovskyD", "TTest123456789012345678901234567890"),
            (123456789, "Alice", "Smith", "alice_smith", "TAlice123456789012345678901234567890"),
            (987654321, "Bob", "Johnson", "bob_johnson", "TBob123456789012345678901234567890"),
            (555666777, "Carol", "Brown", "carol_brown", "TCarol123456789012345678901234567890"),
            (111222333, "David", "Wilson", "david_wilson", "TDavid123456789012345678901234567890"),
            (444555666, "Eve", "Davis", "eve_davis", "TEve123456789012345678901234567890"),
            (777888999, "Frank", "Miller", "frank_miller", "TFrank123456789012345678901234567890")
        ]
        
        print("👥 Создаем тестовых пользователей...")
        for user_id, first_name, last_name, username, wallet_address in test_users:
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (telegram_id, first_name, last_name, username, wallet_address, balance, total_earned)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, first_name, last_name, username, wallet_address, 0.0, 0.0))
        
        # Создаем админа
        cursor.execute('''
            INSERT OR REPLACE INTO admins (telegram_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (739935417, "SulkovskyD", "Dmitry", "Sulkovsky"))
        
        conn.commit()
        print("✅ Пользователи созданы")
        
        # Создаем депозиты с разным количеством в разные дни
        # День 1 (сегодня) - 3 выплаты
        day1_users = test_users[:3]
        amounts1 = [100.0, 50.0, 200.0]
        
        # День 2 (завтра) - 2 выплаты  
        day2_users = test_users[3:5]
        amounts2 = [75.0, 150.0]
        
        # День 3 (послезавтра) - 2 выплаты
        day3_users = test_users[5:7]
        amounts3 = [300.0, 125.0]
        
        print("\n💰 Создаем депозиты с разным количеством в разные дни...")
        
        # День 1 - 3 выплаты
        print("📅 ДЕНЬ 1 (сегодня) - 3 выплаты:")
        for i, (user_id, first_name, last_name, username, wallet_address) in enumerate(day1_users):
            amount = amounts1[i]
            return_amount = amount * 1.1
            print(f"   #{i+1}. {first_name} {last_name} - {amount} USDT -> {return_amount:.2f} USDT")
            
            # Создаем только запись для дня 1
            payment_date = datetime.now()
            cursor.execute('''
                INSERT INTO deposit_payments 
                (user_id, original_amount, return_amount, payment_date, days_remaining, status, wallet_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, return_amount, payment_date.strftime('%Y-%m-%d'), 1, 'pending', wallet_address))
        
        # День 2 - 2 выплаты
        print("\n📅 ДЕНЬ 2 (завтра) - 2 выплаты:")
        for i, (user_id, first_name, last_name, username, wallet_address) in enumerate(day2_users):
            amount = amounts2[i]
            return_amount = amount * 1.1
            print(f"   #{i+1}. {first_name} {last_name} - {amount} USDT -> {return_amount:.2f} USDT")
            
            # Создаем только запись для дня 2
            payment_date = datetime.now() + timedelta(days=1)
            cursor.execute('''
                INSERT INTO deposit_payments 
                (user_id, original_amount, return_amount, payment_date, days_remaining, status, wallet_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, return_amount, payment_date.strftime('%Y-%m-%d'), 2, 'pending', wallet_address))
        
        # День 3 - 2 выплаты
        print("\n📅 ДЕНЬ 3 (послезавтра) - 2 выплаты:")
        for i, (user_id, first_name, last_name, username, wallet_address) in enumerate(day3_users):
            amount = amounts3[i]
            return_amount = amount * 1.1
            print(f"   #{i+1}. {first_name} {last_name} - {amount} USDT -> {return_amount:.2f} USDT")
            
            # Создаем только запись для дня 3
            payment_date = datetime.now() + timedelta(days=2)
            cursor.execute('''
                INSERT INTO deposit_payments 
                (user_id, original_amount, return_amount, payment_date, days_remaining, status, wallet_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, return_amount, payment_date.strftime('%Y-%m-%d'), 3, 'pending', wallet_address))
        
        conn.commit()
        print("\n✅ Все депозиты созданы")
        
        # Показываем статистику
        print(f"\n📊 СТАТИСТИКА:")
        print(f"👥 Пользователей: {len(test_users)}")
        print(f"📅 День 1: 3 выплаты")
        print(f"📅 День 2: 2 выплаты") 
        print(f"📅 День 3: 2 выплаты")

if __name__ == "__main__":
    create_varied_deposits()

















