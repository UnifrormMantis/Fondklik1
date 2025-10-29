#!/usr/bin/env python3
"""
Скрипт для тестирования обработки реферальных выплат
"""

import sqlite3
from datetime import datetime

DATABASE_PATH = "bot_database.db"

def test_referral_processing():
    """Тестировать обработку реферальных выплат"""
    
    print("🧪 ТЕСТИРОВАНИЕ ОБРАБОТКИ РЕФЕРАЛЬНЫХ ВЫПЛАТ")
    print("=" * 50)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Показываем текущее состояние
        print("\n📊 1. ТЕКУЩЕЕ СОСТОЯНИЕ:")
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN transaction_id IS NOT NULL THEN 1 END) as paid,
                COUNT(CASE WHEN transaction_id IS NULL THEN 1 END) as pending
            FROM referral_payments
        ''')
        
        total, paid, pending = cursor.fetchone()
        print(f"• Всего: {total}, Выплачено: {paid}, Ожидает: {pending}")
        
        # 2. Показываем первую ожидающую выплату
        print("\n⏳ 2. ПЕРВАЯ ОЖИДАЮЩАЯ ВЫПЛАТА:")
        cursor.execute('''
            SELECT rp.id, rp.amount, rp.created_at, rp.level, 
                   u1.first_name as referrer_name, u1.wallet_address as referrer_wallet,
                   u2.first_name as referred_name
            FROM referral_payments rp
            JOIN users u1 ON rp.referrer_id = u1.telegram_id
            JOIN users u2 ON rp.referred_id = u2.telegram_id
            WHERE rp.transaction_id IS NULL
            ORDER BY rp.created_at ASC
            LIMIT 1
        ''')
        
        referral = cursor.fetchone()
        if not referral:
            print("❌ Нет ожидающих выплат")
            return
        
        ref_id, amount, created_at, level, referrer_name, referrer_wallet, referred_name = referral
        print(f"• ID: {ref_id}")
        print(f"• Реферер: {referrer_name}")
        print(f"• Кошелек: {referrer_wallet or 'Не указан'}")
        print(f"• Приглашенный: {referred_name}")
        print(f"• Уровень: {level}")
        print(f"• Сумма: {amount:.2f}$")
        print(f"• Дата: {created_at}")
        
        # 3. Симулируем обработку выплаты
        print(f"\n🔄 3. СИМУЛЯЦИЯ ОБРАБОТКИ ВЫПЛАТЫ #{ref_id}:")
        
        try:
            # Получаем referrer_id из реферальной записи
            cursor.execute('''
                SELECT referrer_id FROM referral_payments WHERE id = ?
            ''', (ref_id,))
            referrer_id = cursor.fetchone()[0]
            
            # Создаем транзакцию для реферальной выплаты
            cursor.execute('''
                INSERT INTO transactions (telegram_id, amount, status, created_at)
                VALUES (?, ?, 'completed', CURRENT_TIMESTAMP)
            ''', (referrer_id, amount))
            
            transaction_id = cursor.lastrowid
            print(f"• Создана транзакция #{transaction_id} для пользователя {referrer_id}")
            
            # Обновляем реферальную выплату
            cursor.execute('''
                UPDATE referral_payments 
                SET transaction_id = ? 
                WHERE id = ? AND transaction_id IS NULL
            ''', (transaction_id, ref_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"✅ Выплата #{ref_id} успешно обработана!")
                print(f"• Сумма: {amount:.2f}$")
                print(f"• Транзакция: #{transaction_id}")
                print(f"• Получатель: {referrer_id}")
                
            else:
                print("❌ Заявка не найдена или уже обработана")
                conn.rollback()
                
        except Exception as e:
            print(f"❌ Ошибка при обработке: {e}")
            conn.rollback()
        
        # 4. Показываем обновленное состояние
        print("\n📊 4. ОБНОВЛЕННОЕ СОСТОЯНИЕ:")
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN transaction_id IS NOT NULL THEN 1 END) as paid,
                COUNT(CASE WHEN transaction_id IS NULL THEN 1 END) as pending
            FROM referral_payments
        ''')
        
        total, paid, pending = cursor.fetchone()
        print(f"• Всего: {total}, Выплачено: {paid}, Ожидает: {pending}")
        
        # 5. Показываем следующую ожидающую выплату
        print("\n⏳ 5. СЛЕДУЮЩАЯ ОЖИДАЮЩАЯ ВЫПЛАТА:")
        cursor.execute('''
            SELECT rp.id, rp.amount, rp.created_at, rp.level, 
                   u1.first_name as referrer_name, u2.first_name as referred_name
            FROM referral_payments rp
            JOIN users u1 ON rp.referrer_id = u1.telegram_id
            JOIN users u2 ON rp.referred_id = u2.telegram_id
            WHERE rp.transaction_id IS NULL
            ORDER BY rp.created_at ASC
            LIMIT 1
        ''')
        
        next_referral = cursor.fetchone()
        if next_referral:
            next_id, next_amount, next_created_at, next_level, next_referrer, next_referred = next_referral
            print(f"• ID: {next_id}")
            print(f"• Реферер: {next_referrer} → Приглашенный: {next_referred}")
            print(f"• Сумма: {next_amount:.2f}$ (уровень {next_level})")
            print(f"• Дата: {next_created_at[:16]}")
        else:
            print("✅ Нет больше ожидающих выплат")
        
        # 6. Показываем последние транзакции
        print("\n💳 6. ПОСЛЕДНИЕ ТРАНЗАКЦИИ:")
        cursor.execute('''
            SELECT id, telegram_id, amount, status, created_at
            FROM transactions
            ORDER BY created_at DESC
            LIMIT 3
        ''')
        
        for txn_id, telegram_id, txn_amount, txn_status, txn_created in cursor.fetchall():
            print(f"• #{txn_id}: {txn_amount:.2f}$ ({txn_status}), пользователь {telegram_id}, {txn_created[:16]}")
        
        print("\n✅ ТЕСТИРОВАНИЕ ОБРАБОТКИ ЗАВЕРШЕНО!")

if __name__ == "__main__":
    test_referral_processing()
