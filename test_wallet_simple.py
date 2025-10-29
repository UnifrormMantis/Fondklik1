#!/usr/bin/env python3
"""
Простой тест отображения адресов кошельков
"""

import sqlite3

def test_wallet_display():
    """Тест отображения адресов кошельков"""
    
    print("🔍 Тестируем отображение адресов кошельков в выплатах вкладов")
    
    DATABASE_PATH = "bot_database.db"
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Получаем все выплаты сгруппированные по дням
            cursor.execute('''
                WITH numbered_payments AS (
                    SELECT 
                        dp.days_remaining,
                        dp.payment_date,
                        dp.id,
                        dp.wallet_address,
                        dp.return_amount,
                        ROW_NUMBER() OVER (PARTITION BY dp.days_remaining ORDER BY dp.id) as day_number
                    FROM deposit_payments dp
                    WHERE dp.status = 'pending'
                )
                SELECT 
                    days_remaining,
                    payment_date,
                    COUNT(*) as payment_count,
                    SUM(return_amount) as total_amount,
                    GROUP_CONCAT(
                        '#' || day_number || '. ' || 
                        COALESCE(wallet_address, 'Не указан') || ' - ' || 
                        return_amount || ' USDT - ' || payment_date,
                        '\n'
                    ) as payment_details
                FROM numbered_payments
                GROUP BY days_remaining, payment_date
                ORDER BY days_remaining DESC
            ''')
            
            results = cursor.fetchall()
            print(f"✅ Получено {len(results)} групп выплат")
            
            if not results:
                print("❌ Нет данных о выплатах")
                return
            
            # Показываем результат
            print("\n📋 РЕЗУЛЬТАТ:")
            print("💰 ВЫПЛАТЫ ВКЛАДОВ")
            print()
            print("📅 Расписание по дням:")
            print()
            
            for day_data in results:
                days_remaining, payment_date, payment_count, total_amount, payment_details = day_data
                
                if days_remaining == 1:
                    # Последний день - показываем все детали
                    print(f"🚨 ДЕНЬ {days_remaining} - {payment_date} (СЕГОДНЯ!)")
                    print(f"📊 Количество выплат: {payment_count}")
                    print(f"💰 Общая сумма: {total_amount:.2f} USDT")
                    print()
                    print("👥 ДЕТАЛИ ВЫПЛАТ:")
                    print("─" * 50)
                    print(payment_details)
                    print("─" * 50)
                    print()
                else:
                    # Обычные дни
                    print(f"📅 ДЕНЬ {days_remaining} - {payment_date}")
                    print(f"📊 Количество выплат: {payment_count}")
                    print(f"💰 Общая сумма: {total_amount:.2f} USDT")
                    print()
            
            print("✅ Тест завершен успешно!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_wallet_display()
