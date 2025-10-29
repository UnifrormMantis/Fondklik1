#!/usr/bin/env python3
"""
Полный тест отображения выплат вкладов с 5 заявками
"""

import sqlite3

def test_full_display():
    """Полный тест отображения"""
    
    DATABASE_PATH = "bot_database.db"
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Получаем все выплаты сгруппированные по дням
            cursor.execute('''
                SELECT 
                    dp.days_remaining,
                    dp.payment_date,
                    COUNT(*) as payment_count,
                    SUM(dp.return_amount) as total_amount,
                    GROUP_CONCAT(
                        COALESCE(dp.wallet_address, 'Не указан') || ' - ' || 
                        dp.return_amount || ' USDT - ' || dp.payment_date,
                        '\n'
                    ) as payment_details
                FROM deposit_payments dp
                WHERE dp.status = 'pending'
                GROUP BY dp.days_remaining, dp.payment_date
                ORDER BY dp.days_remaining DESC
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
                    message_text += payment_details + "\n\n"
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
            
            # Показываем статистику
            print(f"\n📊 СТАТИСТИКА:")
            print(f"📅 Всего дней: {len(results)}")
            print(f"👥 Пользователей: {results[0][2] if results else 0}")
            print(f"💰 Общая сумма всех выплат: {sum(day[3] for day in results):.2f} USDT")
            
            # Показываем детали последнего дня
            last_day = results[-1]  # Последний день (день 1)
            print(f"\n🚨 ПОСЛЕДНИЙ ДЕНЬ:")
            print(f"📅 Дата: {last_day[1]}")
            print(f"👥 Количество выплат: {last_day[2]}")
            print(f"💰 Общая сумма: {last_day[3]:.2f} USDT")
            print(f"📋 Детали:\n{last_day[4]}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_display()

















