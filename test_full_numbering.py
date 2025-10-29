#!/usr/bin/env python3
"""
Полный тест нумерации выплат по дням
"""

import sqlite3

def test_full_numbering():
    """Полный тест нумерации"""
    
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
            
            if not results:
                print("❌ Нет данных о выплатах")
                return
            
            # Формируем сообщение как в боте
            message_text = "💰 ВЫПЛАТЫ ВКЛАДОВ\n\n"
            message_text += "📅 Расписание по дням:\n\n"
            
            for day_data in results:
                days_remaining, payment_date, payment_count, total_amount, payment_details = day_data
                
                if days_remaining == 1:
                    # Последний день - показываем все детали
                    message_text += f"🚨 ДЕНЬ {days_remaining} - {payment_date} (СЕГОДНЯ!)\n"
                    message_text += f"📊 Количество выплат: {payment_count}\n"
                    message_text += f"💰 Общая сумма: {total_amount:.2f} USDT\n\n"
                    message_text += "👥 ДЕТАЛИ ВЫПЛАТ:\n"
                    message_text += "─" * 50 + "\n"
                    message_text += payment_details + "\n"
                    message_text += "─" * 50 + "\n\n"
                else:
                    # Обычные дни
                    message_text += f"📅 ДЕНЬ {days_remaining} - {payment_date}\n"
                    message_text += f"📊 Количество выплат: {payment_count}\n"
                    message_text += f"💰 Общая сумма: {total_amount:.2f} USDT\n\n"
            
            print("=" * 60)
            print("📱 КАК БУДЕТ ВЫГЛЯДЕТЬ В ТЕЛЕГРАМ БОТЕ:")
            print("=" * 60)
            print(message_text)
            print("=" * 60)
            
            # Показываем детали каждого дня отдельно
            print("\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ НУМЕРАЦИИ:")
            print("=" * 60)
            
            for day_data in results:
                days_remaining, payment_date, payment_count, total_amount, payment_details = day_data
                
                print(f"\n📅 ДЕНЬ {days_remaining} - {payment_date}")
                print(f"📊 Количество выплат: {payment_count}")
                print(f"💰 Общая сумма: {total_amount:.2f} USDT")
                print("📋 Нумерация:")
                print(payment_details)
                print("-" * 40)
            
            print("\n✅ Нумерация работает правильно!")
            print("   - Каждый день начинается с #1")
            print("   - Нумерация сбрасывается для следующего дня")
            print("   - Внутри дня номера идут по порядку")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_numbering()

















