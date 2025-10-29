#!/usr/bin/env python3
"""
Скрипт для добавления средств пользователю
"""

import sqlite3
from datetime import datetime, timedelta

DATABASE_PATH = 'bot_database.db'

def add_user_funds():
    """Добавить средства пользователю"""
    
    user_id = 798427688
    amount = 1000.0
    wallet_address = "TWJ5wQPnJTk2keYXjEgf19i17ZzACBY4Mx"
    
    print(f"🔧 Добавляем средства пользователю {user_id}")
    print(f"💰 Сумма: {amount} USDT")
    print(f"🏦 Кошелек: {wallet_address}")
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Обновляем баланс пользователя
        print("\n1️⃣ Обновляем баланс пользователя...")
        cursor.execute('''
            UPDATE users 
            SET balance = balance + ?, wallet_address = ?
            WHERE telegram_id = ?
        ''', (amount, wallet_address, user_id))
        
        if cursor.rowcount > 0:
            print(f"✅ Баланс пользователя {user_id} увеличен на {amount} USDT")
        else:
            print(f"❌ Пользователь {user_id} не найден")
            return
        
        # 2. Создаем вклад на последний день (1 день до выплаты)
        print("\n2️⃣ Создаем вклад на последний день...")
        
        # Дата создания (вчера)
        created_at = datetime.now() - timedelta(days=1)
        # Дата выплаты (сегодня)
        payment_date = datetime.now()
        
        # Создаем запись в deposit_payments
        cursor.execute('''
            INSERT INTO deposit_payments 
            (user_id, original_amount, return_amount, days_remaining, status, created_at, payment_date, deposit_type, wallet_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,           # user_id
            amount,            # original_amount
            amount * 1.30,     # return_amount (30% прибыль для 30-дневного депозита)
            1,                 # days_remaining (последний день)
            'pending',         # status
            created_at,        # created_at
            payment_date,      # payment_date
            '30_days',         # deposit_type
            wallet_address     # wallet_address
        ))
        
        deposit_id = cursor.lastrowid
        print(f"✅ Создан вклад ID {deposit_id} на {amount} USDT (30 дней, 30% прибыль)")
        print(f"📅 Дата создания: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Дата выплаты: {payment_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ Дней до выплаты: 1")
        print(f"💰 Сумма к возврату: {amount * 1.30} USDT")
        
        # 3. Обновляем счетчики активных депозитов
        print("\n3️⃣ Обновляем счетчики активных депозитов...")
        cursor.execute('''
            UPDATE users 
            SET active_deposits_30 = active_deposits_30 + 1
            WHERE telegram_id = ?
        ''', (user_id,))
        
        print(f"✅ Счетчик активных 30-дневных депозитов увеличен")
        
        # 4. Создаем запись в user_transactions
        print("\n4️⃣ Создаем запись транзакции...")
        cursor.execute('''
            INSERT INTO user_transactions 
            (user_id, amount, deposit_type, status, wallet_address, invoice_id, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,                    # user_id
            amount,                     # amount
            '30_days',                  # deposit_type
            'success',                  # status
            wallet_address,             # wallet_address
            f'manual_{deposit_id}',     # invoice_id
            datetime.now() + timedelta(hours=1)  # expires_at
        ))
        
        transaction_id = cursor.lastrowid
        print(f"✅ Создана транзакция ID {transaction_id}")
        
        conn.commit()
        
        print(f"\n🎉 ГОТОВО!")
        print(f"👤 Пользователь: {user_id}")
        print(f"💰 Баланс: +{amount} USDT")
        print(f"📊 Вклад: {amount} USDT (30 дней, 30% прибыль)")
        print(f"📅 Статус: Последний день (1 день до выплаты)")
        print(f"🏦 Кошелек: {wallet_address}")
        print(f"💸 Сумма к возврату: {amount * 1.30} USDT")

if __name__ == "__main__":
    add_user_funds()















