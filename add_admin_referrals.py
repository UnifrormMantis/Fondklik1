#!/usr/bin/env python3
"""
Скрипт для добавления рефералов для админов
"""

import sqlite3
import random
from datetime import datetime, timedelta

DATABASE_PATH = "bot_database.db"

def add_admin_referrals():
    """Добавить рефералов для админов"""
    
    print("👑 ДОБАВЛЕНИЕ РЕФЕРАЛОВ ДЛЯ АДМИНОВ")
    print("=" * 50)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Получаем админов
        cursor.execute("SELECT telegram_id, first_name FROM users WHERE telegram_id IN (SELECT telegram_id FROM admins)")
        admins = cursor.fetchall()
        
        if not admins:
            print("❌ Админы не найдены")
            return
        
        print(f"👑 Найдено {len(admins)} админов:")
        for admin_id, admin_name in admins:
            print(f"  • {admin_name} (ID: {admin_id})")
        
        # Получаем всех пользователей для создания рефералов
        cursor.execute("SELECT telegram_id, first_name FROM users")
        all_users = cursor.fetchall()
        
        if len(all_users) < 3:
            print("❌ Недостаточно пользователей для создания рефералов")
            return
        
        print(f"📊 Всего пользователей: {len(all_users)}")
        
        # Создаем реферальные записи для админов
        referral_data = []
        
        # Для каждого админа создаем 8-12 рефералов
        for admin_id, admin_name in admins:
            num_referrals = random.randint(8, 12)
            print(f"\n🎯 Создаю {num_referrals} рефералов для {admin_name}...")
            
            for i in range(num_referrals):
                # Выбираем случайного пользователя (не админа)
                referred = random.choice([u for u in all_users if u[0] != admin_id])
                
                # Случайные параметры
                level = random.choice([1, 2])  # 1-й или 2-й уровень
                amount = round(random.uniform(50, 1000), 2)  # Сумма от 50 до 1000
                percentage = 5.0 if level == 1 else 2.0  # 5% для 1-го уровня, 2% для 2-го
                
                # Случайная дата в последние 20 дней
                days_ago = random.randint(0, 20)
                created_at = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
                
                # 60% активных рефералов, 40% уже выплаченных
                transaction_id = random.randint(1, 100) if random.random() < 0.4 else None
                
                referral_data.append((
                    admin_id,      # referrer_id (админ)
                    referred[0],   # referred_id
                    level,         # level
                    amount,        # amount
                    percentage,    # percentage
                    transaction_id,  # transaction_id
                    created_at     # created_at
                ))
        
        # Вставляем данные
        cursor.executemany('''
            INSERT INTO referral_payments 
            (referrer_id, referred_id, level, amount, percentage, transaction_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', referral_data)
        
        conn.commit()
        
        print(f"\n✅ Добавлено {len(referral_data)} реферальных записей для админов")
        
        # Показываем статистику по админам
        print("\n👑 СТАТИСТИКА ПО АДМИНАМ:")
        cursor.execute('''
            SELECT 
                u.first_name,
                COUNT(rp.id) as total_referrals,
                COUNT(CASE WHEN rp.transaction_id IS NULL THEN 1 END) as active_referrals,
                COUNT(CASE WHEN rp.transaction_id IS NOT NULL THEN 1 END) as paid_referrals,
                SUM(rp.amount) as total_amount,
                SUM(CASE WHEN rp.transaction_id IS NULL THEN rp.amount ELSE 0 END) as active_amount,
                SUM(CASE WHEN rp.transaction_id IS NOT NULL THEN rp.amount ELSE 0 END) as paid_amount
            FROM referral_payments rp
            JOIN users u ON rp.referrer_id = u.telegram_id
            WHERE rp.referrer_id IN (SELECT telegram_id FROM admins)
            GROUP BY rp.referrer_id, u.first_name
            ORDER BY total_referrals DESC
        ''')
        
        for name, total, active, paid, total_amount, active_amount, paid_amount in cursor.fetchall():
            print(f"• {name}:")
            print(f"  - Всего рефералов: {total}")
            print(f"  - Активных: {active} ({active_amount:.2f}$)")
            print(f"  - Выплаченных: {paid} ({paid_amount:.2f}$)")
            print(f"  - Общая сумма: {total_amount:.2f}$")
            print()
        
        # Показываем примеры активных рефералов админов
        print("⏳ ПРИМЕРЫ АКТИВНЫХ РЕФЕРАЛОВ АДМИНОВ:")
        cursor.execute('''
            SELECT rp.id, rp.amount, rp.created_at, rp.level, 
                   u1.first_name as admin_name, u2.first_name as referred_name
            FROM referral_payments rp
            JOIN users u1 ON rp.referrer_id = u1.telegram_id
            JOIN users u2 ON rp.referred_id = u2.telegram_id
            WHERE rp.transaction_id IS NULL AND rp.referrer_id IN (SELECT telegram_id FROM admins)
            ORDER BY rp.created_at DESC
            LIMIT 5
        ''')
        
        for ref_id, amount, created_at, level, admin_name, referred_name in cursor.fetchall():
            print(f"• #{ref_id}: {admin_name} → {referred_name}, {amount:.2f}$ (уровень {level}), {created_at[:16]}")
        
        # Общая статистика
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN transaction_id IS NULL THEN 1 END) as pending,
                COUNT(CASE WHEN transaction_id IS NOT NULL THEN 1 END) as paid,
                SUM(amount) as total_amount
            FROM referral_payments
        ''')
        
        total, pending, paid, total_amount = cursor.fetchone()
        print(f"\n📊 ОБЩАЯ СТАТИСТИКА РЕФЕРАЛОВ:")
        print(f"• Всего записей: {total}")
        print(f"• Ожидает выплаты: {pending}")
        print(f"• Выплачено: {paid}")
        print(f"• Общая сумма: {total_amount:.2f}$")

if __name__ == "__main__":
    add_admin_referrals()






