#!/usr/bin/env python3
"""
Тестовый скрипт для создания второго тестового вклада
"""

import sqlite3
from datetime import datetime, timedelta

DATABASE_PATH = "bot_database.db"

def create_test_deposit2():
    """Создать второй тестовый вклад для демонстрации группировки"""
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Находим первого пользователя
        user = cursor.execute('SELECT telegram_id FROM users LIMIT 1').fetchone()
        if not user:
            print("❌ Нет пользователей в базе данных")
            return
        
        user_id = user[0]
        amount = 50.0  # 50 USDT
        
        print(f"💰 Создаем второй тестовый вклад для пользователя {user_id}: {amount} USDT")
        
        # Рассчитываем сумму к возврату (100% + 10% = 110%)
        return_amount = amount * 1.1
        
        # Создаем записи для каждого дня (10, 9, 8, ..., 1)
        for days_remaining in range(10, 0, -1):
            payment_date = datetime.now() + timedelta(days=10 - days_remaining)
            
            cursor.execute('''
                INSERT INTO deposit_payments 
                (user_id, original_amount, return_amount, payment_date, days_remaining, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, return_amount, payment_date.strftime('%Y-%m-%d'), days_remaining, 'pending'))
        
        conn.commit()
        print(f"✅ Создано расписание выплат: {amount} USDT -> {return_amount:.2f} USDT за 10 дней")
        
        # Показываем общую статистику
        cursor.execute('''
            SELECT 
                days_remaining,
                payment_date,
                COUNT(*) as payment_count,
                SUM(return_amount) as total_amount
            FROM deposit_payments 
            WHERE status = 'pending'
            GROUP BY days_remaining, payment_date
            ORDER BY days_remaining DESC
        ''')
        
        results = cursor.fetchall()
        print("\n📊 Общая статистика выплат:")
        for days_remaining, payment_date, payment_count, total_amount in results:
            if days_remaining == 1:
                print(f"🚨 ДЕНЬ {days_remaining} - {payment_date} (СЕГОДНЯ!) - {payment_count} выплат - {total_amount:.2f} USDT")
            else:
                print(f"📅 ДЕНЬ {days_remaining} - {payment_date} - {payment_count} выплат - {total_amount:.2f} USDT")

if __name__ == "__main__":
    create_test_deposit2()

















