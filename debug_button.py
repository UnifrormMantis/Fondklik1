#!/usr/bin/env python3
"""
Отладка кнопки "Выплата вкладов"
"""

import sqlite3

DATABASE_PATH = "bot_database.db"

def debug_deposit_payments():
    """Отладка системы выплат вкладов"""
    
    print("🔍 ОТЛАДКА СИСТЕМЫ ВЫПЛАТ ВКЛАДОВ")
    print("=" * 50)
    
    # 1. Проверяем таблицу deposit_payments
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы
        cursor.execute("PRAGMA table_info(deposit_payments)")
        columns = cursor.fetchall()
        print("📊 Структура таблицы deposit_payments:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Проверяем количество записей
        cursor.execute("SELECT COUNT(*) FROM deposit_payments")
        count = cursor.fetchone()[0]
        print(f"\n📈 Всего записей в deposit_payments: {count}")
        
        # Проверяем статусы
        cursor.execute("SELECT status, COUNT(*) FROM deposit_payments GROUP BY status")
        statuses = cursor.fetchall()
        print("📊 Статусы записей:")
        for status, count in statuses:
            print(f"   - {status}: {count}")
        
        # Проверяем админов
        cursor.execute("SELECT COUNT(*) FROM admins")
        admin_count = cursor.fetchone()[0]
        print(f"\n👥 Количество админов: {admin_count}")
        
        # Проверяем конкретного админа
        admin_id = 739935417
        cursor.execute("SELECT * FROM admins WHERE telegram_id = ?", (admin_id,))
        admin = cursor.fetchone()
        if admin:
            print(f"✅ Админ {admin_id} найден: {admin[1]} ({admin[2]})")
        else:
            print(f"❌ Админ {admin_id} не найден")
        
        # Тестируем запрос
        print("\n🔍 Тестируем SQL запрос...")
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
            print(f"✅ SQL запрос выполнен успешно, получено {len(results)} результатов")
            
            if results:
                print("📋 Первый результат:")
                print(f"   - День: {results[0][0]}")
                print(f"   - Дата: {results[0][1]}")
                print(f"   - Количество: {results[0][2]}")
                print(f"   - Сумма: {results[0][3]}")
                print(f"   - Детали: {results[0][4][:100]}...")
            
        except Exception as e:
            print(f"❌ Ошибка в SQL запросе: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_deposit_payments()

















