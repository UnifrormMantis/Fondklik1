#!/usr/bin/env python3
"""
Тест обновленной админ-панели выплат вкладов
"""

import sqlite3

def test_admin_payments():
    """Тест админ-панели выплат"""
    
    DATABASE_PATH = "bot_database.db"
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            print("🔍 Тестируем обновленную админ-панель выплат вкладов")
            
            # Получаем выплаты для 10-дневных депозитов
            cursor.execute('''
                WITH numbered_payments AS (
                    SELECT 
                        dp.days_remaining,
                        dp.payment_date,
                        dp.id,
                        dp.wallet_address,
                        dp.return_amount,
                        dp.deposit_type,
                        ROW_NUMBER() OVER (PARTITION BY dp.days_remaining, dp.deposit_type ORDER BY dp.id) as day_number
                    FROM deposit_payments dp
                    WHERE dp.status = 'pending' AND dp.deposit_type = '10_days'
                )
                SELECT 
                    days_remaining,
                    payment_date,
                    deposit_type,
                    COUNT(*) as payment_count,
                    SUM(return_amount) as total_amount,
                    GROUP_CONCAT(
                        '#' || day_number || '. ' || 
                        COALESCE(wallet_address, 'Не указан') || ' - ' || 
                        return_amount || ' USDT - ' || payment_date || ' (' || deposit_type || ')',
                        '\n'
                    ) as payment_details
                FROM numbered_payments
                GROUP BY days_remaining, payment_date, deposit_type
                ORDER BY days_remaining DESC
            ''')
            
            payments_10_days = cursor.fetchall()
            
            # Получаем выплаты для 30-дневных депозитов
            cursor.execute('''
                WITH numbered_payments AS (
                    SELECT 
                        dp.days_remaining,
                        dp.payment_date,
                        dp.id,
                        dp.wallet_address,
                        dp.return_amount,
                        dp.deposit_type,
                        ROW_NUMBER() OVER (PARTITION BY dp.days_remaining, dp.deposit_type ORDER BY dp.id) as day_number
                    FROM deposit_payments dp
                    WHERE dp.status = 'pending' AND dp.deposit_type = '30_days'
                )
                SELECT 
                    days_remaining,
                    payment_date,
                    deposit_type,
                    COUNT(*) as payment_count,
                    SUM(return_amount) as total_amount,
                    GROUP_CONCAT(
                        '#' || day_number || '. ' || 
                        COALESCE(wallet_address, 'Не указан') || ' - ' || 
                        return_amount || ' USDT - ' || payment_date || ' (' || deposit_type || ')',
                        '\n'
                    ) as payment_details
                FROM numbered_payments
                GROUP BY days_remaining, payment_date, deposit_type
                ORDER BY days_remaining DESC
            ''')
            
            payments_30_days = cursor.fetchall()
            
            print(f"✅ Получено {len(payments_10_days)} групп 10-дневных выплат")
            print(f"✅ Получено {len(payments_30_days)} групп 30-дневных выплат")
            
            # Формируем сообщение как в боте
            message_text = "💰 ВЫПЛАТЫ ВКЛАДОВ\n\n"
            
            # Показываем 10-дневные депозиты
            if payments_10_days:
                message_text += "📅 10-ДНЕВНЫЕ ДЕПОЗИТЫ (8% прибыль):\n\n"
                
                for day_data in payments_10_days:
                    days_remaining, payment_date, deposit_type, payment_count, total_amount, payment_details = day_data
                    
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
            
            # Показываем 30-дневные депозиты
            if payments_30_days:
                message_text += "📅 30-ДНЕВНЫЕ ДЕПОЗИТЫ (30% прибыль):\n\n"
                
                for day_data in payments_30_days:
                    days_remaining, payment_date, deposit_type, payment_count, total_amount, payment_details = day_data
                    
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
            
            print("\n" + "=" * 60)
            print("📱 КАК БУДЕТ ВЫГЛЯДЕТЬ В АДМИН-ПАНЕЛИ:")
            print("=" * 60)
            print(message_text)
            print("=" * 60)
            
            print("\n✅ Тест админ-панели завершен успешно!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_admin_payments()
















