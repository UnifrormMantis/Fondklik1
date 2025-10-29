#!/usr/bin/env python3
"""
Скрипт для проверки депозитов правильного админа
"""

import sqlite3

DATABASE_PATH = 'bot_database.db'

def check_correct_admin():
    """Проверить депозиты правильного админа"""
    
    admin_id = 739935417  # Правильный ID админа
    
    print(f"🔍 Проверяем депозиты правильного админа {admin_id}")
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Проверяем есть ли пользователь в базе
        print("\n1️⃣ Проверяем пользователя в базе...")
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (admin_id,))
        user = cursor.fetchone()
        
        if user:
            print(f"✅ Пользователь найден: {user}")
        else:
            print(f"❌ Пользователь {admin_id} не найден в базе")
            print("💡 Нужно создать пользователя или добавить его в базу")
            return
        
        # 2. Проверяем активные депозиты
        print("\n2️⃣ Проверяем активные депозиты...")
        cursor.execute('''
            SELECT dp.id, dp.original_amount, dp.deposit_type, dp.days_remaining, dp.created_at, dp.status
            FROM deposit_payments dp
            WHERE dp.user_id = ? AND dp.status = 'pending'
            ORDER BY dp.created_at DESC
        ''', (admin_id,))
        
        active_deposits = cursor.fetchall()
        
        if active_deposits:
            print(f"✅ Найдено {len(active_deposits)} активных депозитов:")
            for deposit in active_deposits:
                print(f"   ID: {deposit[0]}, Сумма: {deposit[1]} USDT, Тип: {deposit[2]}, Дней: {deposit[3]}, Дата: {deposit[4]}, Статус: {deposit[5]}")
        else:
            print("❌ Активных депозитов не найдено")
        
        # 3. Проверяем выплаченные депозиты
        print("\n3️⃣ Проверяем выплаченные депозиты...")
        cursor.execute('''
            SELECT dp.id, dp.original_amount, dp.deposit_type, dp.payment_date, dp.return_amount, dp.status
            FROM deposit_payments dp
            WHERE dp.user_id = ? AND dp.status = 'paid'
            ORDER BY dp.payment_date DESC
        ''', (admin_id,))
        
        paid_deposits = cursor.fetchall()
        
        if paid_deposits:
            print(f"✅ Найдено {len(paid_deposits)} выплаченных депозитов:")
            for deposit in paid_deposits:
                print(f"   ID: {deposit[0]}, Сумма: {deposit[1]} USDT, Тип: {deposit[2]}, Дата выплаты: {deposit[3]}, Возврат: {deposit[4]} USDT, Статус: {deposit[5]}")
        else:
            print("❌ Выплаченных депозитов не найдено")
        
        # 4. Проверяем все депозиты
        print("\n4️⃣ Проверяем все депозиты...")
        cursor.execute('''
            SELECT dp.id, dp.original_amount, dp.deposit_type, dp.days_remaining, dp.created_at, dp.status
            FROM deposit_payments dp
            WHERE dp.user_id = ?
            ORDER BY dp.created_at DESC
        ''', (admin_id,))
        
        all_deposits = cursor.fetchall()
        
        if all_deposits:
            print(f"✅ Всего депозитов: {len(all_deposits)}")
            for deposit in all_deposits:
                print(f"   ID: {deposit[0]}, Сумма: {deposit[1]} USDT, Тип: {deposit[2]}, Дней: {deposit[3]}, Дата: {deposit[4]}, Статус: {deposit[5]}")
        else:
            print("❌ Депозитов не найдено")
        
        # 5. Проверяем транзакции
        print("\n5️⃣ Проверяем транзакции...")
        cursor.execute('''
            SELECT ut.id, ut.amount, ut.deposit_type, ut.status, ut.wallet_address, ut.created_at
            FROM user_transactions ut
            WHERE ut.user_id = ?
            ORDER BY ut.created_at DESC
        ''', (admin_id,))
        
        transactions = cursor.fetchall()
        
        if transactions:
            print(f"✅ Найдено {len(transactions)} транзакций:")
            for transaction in transactions:
                print(f"   ID: {transaction[0]}, Сумма: {transaction[1]} USDT, Тип: {transaction[2]}, Статус: {transaction[3]}, Кошелек: {transaction[4]}, Дата: {transaction[5]}")
        else:
            print("❌ Транзакций не найдено")

if __name__ == "__main__":
    check_correct_admin()















