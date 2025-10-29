#!/usr/bin/env python3
"""
Создание правильных тестовых данных для выплат вкладов
"""

import sqlite3
from datetime import datetime, timedelta

DATABASE_PATH = "bot_database.db"

def create_correct_deposits():
    """Создать правильные тестовые данные"""
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Находим первого пользователя
        user = cursor.execute('SELECT telegram_id FROM users LIMIT 1').fetchone()
        if not user:
            print("❌ Нет пользователей в базе данных")
            return
        
        user_id = user[0]
        amount = 100.0  # 100 USDT
        
        print(f"💰 Создаем правильные тестовые данные для пользователя {user_id}: {amount} USDT")
        print(f"📅 Сегодня: {datetime.now().strftime('%Y-%m-%d')}")
        
        # Рассчитываем сумму к возврату (100% + 10% = 110%)
        return_amount = amount * 1.1
        
        # Создаем записи для каждого дня (10, 9, 8, ..., 1)
        for days_remaining in range(10, 0, -1):
            payment_date = datetime.now() + timedelta(days=days_remaining - 1)
            
            cursor.execute('''
                INSERT INTO deposit_payments 
                (user_id, original_amount, return_amount, payment_date, days_remaining, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, return_amount, payment_date.strftime('%Y-%m-%d'), days_remaining, 'pending'))
            
            print(f"   ДЕНЬ {days_remaining} - {payment_date.strftime('%Y-%m-%d')} - {return_amount:.2f} USDT")
        
        conn.commit()
        print(f"✅ Создано правильное расписание выплат: {amount} USDT -> {return_amount:.2f} USDT за 10 дней")
        
        # Показываем правильное расписание
        print("\n📅 ПРАВИЛЬНОЕ РАСПИСАНИЕ ВЫПЛАТ:")
        cursor.execute('''
            SELECT days_remaining, payment_date, return_amount
            FROM deposit_payments 
            WHERE user_id = ? AND original_amount = ?
            ORDER BY days_remaining DESC
        ''', (user_id, amount))
        
        results = cursor.fetchall()
        for days_remaining, payment_date, return_amount in results:
            if days_remaining == 1:
                print(f"🚨 ДЕНЬ {days_remaining} - {payment_date} (СЕГОДНЯ!) - {return_amount:.2f} USDT")
            else:
                print(f"📅 ДЕНЬ {days_remaining} - {payment_date} - {return_amount:.2f} USDT")

if __name__ == "__main__":
    create_correct_deposits()

















