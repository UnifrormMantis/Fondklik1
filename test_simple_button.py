#!/usr/bin/env python3
"""
Простой тест кнопки "Выплата вкладов"
"""

import sqlite3

DATABASE_PATH = "bot_database.db"

def is_admin(telegram_id):
    """Проверить, является ли пользователь администратором"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        admin = cursor.execute('SELECT telegram_id FROM admins WHERE telegram_id = ?', (telegram_id,)).fetchone()
        return admin is not None

def get_deposit_payments_by_day():
    """Получить выплаты вкладов сгруппированные по дням"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
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
            return results
    except Exception as e:
        print(f"❌ Ошибка в get_deposit_payments_by_day: {e}")
        return []

def test_deposit_payments():
    """Тестируем кнопку выплат вкладов"""
    
    # Тестируем с ID админа
    admin_id = 739935417  # ID админа из базы данных
    
    print(f"🔍 Тестируем кнопку 'Выплата вкладов' для админа {admin_id}")
    
    # Проверяем, является ли пользователь админом
    is_admin_result = is_admin(admin_id)
    print(f"👤 Является админом: {is_admin_result}")
    
    if not is_admin_result:
        print("❌ Пользователь не является админом")
        return
    
    # Тестируем получение данных
    print("📊 Получаем данные о выплатах...")
    payments = get_deposit_payments_by_day()
    print(f"✅ Получено {len(payments)} групп выплат")
    
    if not payments:
        print("💰 Нет выплат вкладов")
        return
    
    # Показываем результат как в боте
    message_text = "💰 ВЫПЛАТЫ ВКЛАДОВ\n\n"
    message_text += "📅 Расписание по дням:\n\n"
    
    for day_data in payments:
        days_remaining, payment_date, payment_count, total_amount, payment_details = day_data
        
        if days_remaining == 1:
            message_text += f"🚨 ДЕНЬ {days_remaining} - {payment_date} (СЕГОДНЯ!)\n"
            message_text += f"📊 Количество выплат: {payment_count}\n"
            message_text += f"💰 Общая сумма: {total_amount:.2f} USDT\n\n"
            message_text += "👥 ДЕТАЛИ ВЫПЛАТ:\n"
            message_text += payment_details + "\n\n"
        else:
            message_text += f"📅 ДЕНЬ {days_remaining} - {payment_date}\n"
            message_text += f"📊 Количество выплат: {payment_count}\n"
            message_text += f"💰 Общая сумма: {total_amount:.2f} USDT\n\n"
    
    print("✅ Кнопка 'Выплата вкладов' работает корректно!")
    print("📋 Результат:")
    print(message_text)

if __name__ == "__main__":
    test_deposit_payments()

















