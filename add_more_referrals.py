#!/usr/bin/env python3
"""
Скрипт для добавления большего количества активных рефералов разных уровней
"""

import sqlite3
import random
from datetime import datetime, timedelta

DATABASE_PATH = "bot_database.db"

def add_more_referrals():
    """Добавить больше активных рефералов разных уровней"""
    
    print("🎯 ДОБАВЛЕНИЕ АКТИВНЫХ РЕФЕРАЛОВ")
    print("=" * 50)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Получаем существующих пользователей
        cursor.execute("SELECT telegram_id, first_name FROM users LIMIT 15")
        users = cursor.fetchall()
        
        if len(users) < 5:
            print("❌ Недостаточно пользователей для создания рефералов")
            return
        
        print(f"📊 Найдено {len(users)} пользователей")
        
        # Создаем реферальные записи
        referral_data = []
        
        # Создаем 30 новых реферальных записей (5-8 на каждого пользователя)
        for i in range(30):
            # Выбираем случайного реферера и реферала
            referrer = random.choice(users)
            referred = random.choice([u for u in users if u[0] != referrer[0]])
            
            # Случайные параметры
            level = random.choice([1, 2])  # 1-й или 2-й уровень
            amount = round(random.uniform(30, 800), 2)  # Сумма от 30 до 800
            percentage = 5.0 if level == 1 else 2.0  # 5% для 1-го уровня, 2% для 2-го
            
            # Случайная дата в последние 15 дней (более свежие данные)
            days_ago = random.randint(0, 15)
            created_at = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Большинство записей делаем активными (без transaction_id)
            # 70% активных, 30% уже выплаченных
            transaction_id = random.randint(1, 100) if random.random() < 0.3 else None
            
            referral_data.append((
                referrer[0],  # referrer_id
                referred[0],  # referred_id
                level,        # level
                amount,       # amount
                percentage,   # percentage
                transaction_id,  # transaction_id
                created_at    # created_at
            ))
        
        # Вставляем данные
        cursor.executemany('''
            INSERT INTO referral_payments 
            (referrer_id, referred_id, level, amount, percentage, transaction_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', referral_data)
        
        conn.commit()
        
        print(f"✅ Добавлено {len(referral_data)} новых реферальных записей")
        
        # Показываем обновленную статистику
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN transaction_id IS NOT NULL THEN 1 END) as paid,
                COUNT(CASE WHEN transaction_id IS NULL THEN 1 END) as pending,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount
            FROM referral_payments
        ''')
        
        stats = cursor.fetchone()
        print(f"""
📊 ОБНОВЛЕННАЯ СТАТИСТИКА РЕФЕРАЛОВ:
• Всего записей: {stats[0]}
• Выплачено: {stats[1]}
• Ожидает выплаты: {stats[2]}
• Общая сумма: {stats[3]:.2f}$
• Средняя сумма: {stats[4]:.2f}$
        """)
        
        # Статистика по уровням
        print("\n🎯 СТАТИСТИКА ПО УРОВНЯМ:")
        cursor.execute('''
            SELECT 
                level,
                COUNT(*) as count,
                COUNT(CASE WHEN transaction_id IS NULL THEN 1 END) as pending,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount
            FROM referral_payments
            GROUP BY level
            ORDER BY level
        ''')
        
        for level, count, pending, total, avg in cursor.fetchall():
            print(f"• Уровень {level}: {count} записей ({pending} активных), {total:.2f}$ (среднее: {avg:.2f}$)")
        
        # Топ рефереров по количеству активных рефералов
        print("\n👑 ТОП РЕФЕРЕРОВ ПО АКТИВНЫМ РЕФЕРАЛАМ:")
        cursor.execute('''
            SELECT 
                u.first_name,
                COUNT(rp.id) as total_referrals,
                COUNT(CASE WHEN rp.transaction_id IS NULL THEN 1 END) as active_referrals,
                SUM(rp.amount) as total_amount,
                SUM(CASE WHEN rp.transaction_id IS NULL THEN rp.amount ELSE 0 END) as active_amount
            FROM referral_payments rp
            JOIN users u ON rp.referrer_id = u.telegram_id
            GROUP BY rp.referrer_id, u.first_name
            HAVING COUNT(CASE WHEN rp.transaction_id IS NULL THEN 1 END) > 0
            ORDER BY active_referrals DESC, active_amount DESC
            LIMIT 8
        ''')
        
        for name, total, active, total_amount, active_amount in cursor.fetchall():
            print(f"• {name}: {active}/{total} активных рефералов, {active_amount:.2f}$ активных из {total_amount:.2f}$")
        
        # Показываем несколько примеров активных рефералов
        print("\n⏳ ПРИМЕРЫ АКТИВНЫХ РЕФЕРАЛОВ:")
        cursor.execute('''
            SELECT rp.id, rp.amount, rp.created_at, rp.level, 
                   u1.first_name as referrer_name, u2.first_name as referred_name
            FROM referral_payments rp
            JOIN users u1 ON rp.referrer_id = u1.telegram_id
            JOIN users u2 ON rp.referred_id = u2.telegram_id
            WHERE rp.transaction_id IS NULL
            ORDER BY rp.created_at DESC
            LIMIT 5
        ''')
        
        for ref_id, amount, created_at, level, referrer, referred in cursor.fetchall():
            print(f"• #{ref_id}: {referrer} → {referred}, {amount:.2f}$ (уровень {level}), {created_at[:16]}")

if __name__ == "__main__":
    add_more_referrals()






