#!/usr/bin/env python3
"""
Создание множественных тестовых данных для выплат вкладов
"""

import sqlite3
from datetime import datetime, timedelta

DATABASE_PATH = "bot_database.db"

def create_multiple_deposits():
    """Создать множественные тестовые данные"""
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Создаем тестовых пользователей если их нет
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
        
        # Очищаем старые данные
        cursor.execute("DELETE FROM deposit_payments")
        print("🗑️ Старые данные очищены")
        
        # Создаем депозиты для каждого пользователя
        amounts = [100.0, 50.0, 200.0, 75.0, 150.0]  # Разные суммы
        
        print("\n💰 Создаем депозиты...")
        for i, (user_id, first_name, last_name, username, wallet_address) in enumerate(test_users):
            amount = amounts[i]
            return_amount = amount * 1.1
            
            print(f"   {first_name} {last_name} - {amount} USDT -> {return_amount:.2f} USDT")
            
            # Создаем записи для каждого дня (10, 9, 8, ..., 1)
            for days_remaining in range(10, 0, -1):
                payment_date = datetime.now() + timedelta(days=days_remaining - 1)
                
                cursor.execute('''
                    INSERT INTO deposit_payments 
                    (user_id, original_amount, return_amount, payment_date, days_remaining, status, wallet_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, amount, return_amount, payment_date.strftime('%Y-%m-%d'), days_remaining, 'pending', wallet_address))
        
        conn.commit()
        print("✅ Все депозиты созданы")
        
        # Показываем статистику
        print(f"\n📊 СТАТИСТИКА:")
        print(f"👥 Пользователей: {len(test_users)}")
        print(f"💰 Общая сумма вкладов: {sum(amounts):.2f} USDT")
        print(f"💸 Общая сумма к возврату: {sum(amounts) * 1.1:.2f} USDT")
        
        # Показываем что будет на последний день
        print(f"\n🚨 ПОСЛЕДНИЙ ДЕНЬ (СЕГОДНЯ - {datetime.now().strftime('%Y-%m-%d')}):")
        cursor.execute('''
            SELECT dp.wallet_address, dp.return_amount, u.first_name, u.last_name
            FROM deposit_payments dp
            JOIN users u ON dp.user_id = u.telegram_id
            WHERE dp.days_remaining = 1
            ORDER BY dp.return_amount DESC
        ''')
        
        last_day_payments = cursor.fetchall()
        total_last_day = sum(payment[1] for payment in last_day_payments)
        
        print(f"📊 Количество выплат: {len(last_day_payments)}")
        print(f"💰 Общая сумма: {total_last_day:.2f} USDT")
        print("\n👥 ДЕТАЛИ ВЫПЛАТ:")
        for wallet_address, return_amount, first_name, last_name in last_day_payments:
            print(f"   {wallet_address} - {return_amount:.2f} USDT ({first_name} {last_name})")

if __name__ == "__main__":
    create_multiple_deposits()

















