#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы выплат вкладов
"""

import sqlite3

DATABASE_PATH = "bot_database.db"

def test_deposit_payments():
    """Тестируем систему выплат вкладов"""
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Проверяем, есть ли данные в таблице
        cursor.execute('SELECT COUNT(*) FROM deposit_payments')
        count = cursor.fetchone()[0]
        print(f"📊 Всего записей в deposit_payments: {count}")
        
        if count == 0:
            print("❌ Нет данных в таблице deposit_payments")
            return
        
        # Тестируем запрос из get_deposit_payments_by_day
        try:
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
            print(f"✅ Запрос выполнен успешно, получено {len(results)} групп")
            
            for day_data in results:
                days_remaining, payment_date, payment_count, total_amount, payment_details = day_data
                print(f"📅 ДЕНЬ {days_remaining} - {payment_date}")
                print(f"   Количество: {payment_count}, Сумма: {total_amount:.2f} USDT")
                if payment_details:
                    print(f"   Детали: {payment_details[:100]}...")
                print()
                
        except Exception as e:
            print(f"❌ Ошибка в запросе: {e}")

if __name__ == "__main__":
    test_deposit_payments()

















