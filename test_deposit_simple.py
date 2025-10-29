#!/usr/bin/env python3
"""
Простое тестирование системы выплат вкладов
"""

import sqlite3

DATABASE_PATH = "bot_database.db"

def test_deposit_payments_simple():
    """Простое тестирование системы выплат"""
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Тестируем запрос
        cursor.execute('''
            SELECT 
                dp.days_remaining,
                dp.payment_date,
                COUNT(*) as payment_count,
                SUM(dp.return_amount) as total_amount,
                GROUP_CONCAT(
                    u.first_name || ' ' || COALESCE(u.last_name, '') || ' (@' || COALESCE(u.username, 'no_username') || ') - ' || 
                    dp.return_amount || ' USDT - ' || dp.payment_date,
                    '\n'
                ) as payment_details
            FROM deposit_payments dp
            JOIN users u ON dp.user_id = u.telegram_id
            WHERE dp.status = 'pending'
            GROUP BY dp.days_remaining, dp.payment_date
            ORDER BY dp.days_remaining DESC
        ''')
        
        results = cursor.fetchall()
        
        if not results:
            print("💰 Нет выплат вкладов")
            return
        
        print("💰 ВЫПЛАТЫ ВКЛАДОВ\n")
        print("📅 Расписание по дням:\n")
        
        for day_data in results:
            days_remaining, payment_date, payment_count, total_amount, payment_details = day_data
            
            if days_remaining == 1:
                print(f"🚨 ДЕНЬ {days_remaining} - {payment_date} (СЕГОДНЯ!)")
                print(f"📊 Количество выплат: {payment_count}")
                print(f"💰 Общая сумма: {total_amount:.2f} USDT\n")
                print("👥 ДЕТАЛИ ВЫПЛАТ:")
                print(payment_details + "\n")
            else:
                print(f"📅 ДЕНЬ {days_remaining} - {payment_date}")
                print(f"📊 Количество выплат: {payment_count}")
                print(f"💰 Общая сумма: {total_amount:.2f} USDT\n")

if __name__ == "__main__":
    test_deposit_payments_simple()

















