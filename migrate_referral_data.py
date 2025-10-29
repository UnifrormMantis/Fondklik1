#!/usr/bin/env python3
"""
Миграция данных в новую реферальную систему
"""

import sqlite3
import random
import string
from datetime import datetime, timedelta

DATABASE_PATH = "bot_database.db"

def generate_referral_code():
    """Генерировать уникальный реферальный код"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def migrate_referral_data():
    """Мигрировать данные в новую систему"""
    
    print("🔄 МИГРАЦИЯ ДАННЫХ В НОВУЮ РЕФЕРАЛЬНУЮ СИСТЕМУ")
    print("=" * 50)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Генерируем реферальные коды для всех пользователей
        print("🔑 1. Генерация реферальных кодов...")
        cursor.execute("SELECT telegram_id FROM users")
        users = cursor.fetchall()
        
        referral_codes = set()
        for user_id, in users:
            while True:
                code = generate_referral_code()
                if code not in referral_codes:
                    referral_codes.add(code)
                    break
            
            cursor.execute('''
                UPDATE users SET referral_code = ? WHERE telegram_id = ?
            ''', (code, user_id))
        
        print(f"  ✅ Сгенерировано {len(users)} реферальных кодов")
        
        # 2. Создаем реферальные связи на основе существующих данных
        print("\n🔗 2. Создание реферальных связей...")
        
        # Получаем существующие связи из referral_payments
        cursor.execute('''
            SELECT DISTINCT referrer_id, referred_id 
            FROM referral_payments 
            WHERE referrer_id IS NOT NULL AND referred_id IS NOT NULL
        ''')
        existing_connections = cursor.fetchall()
        
        # Создаем связи 1-го уровня
        for referrer_id, referred_id in existing_connections:
            cursor.execute('''
                INSERT OR IGNORE INTO referral_network (referrer_id, referred_id, level)
                VALUES (?, ?, 1)
            ''', (referrer_id, referred_id))
            
            # Обновляем referrer_id в таблице users
            cursor.execute('''
                UPDATE users SET referrer_id = ? WHERE telegram_id = ?
            ''', (referrer_id, referred_id))
        
        # Создаем связи 2-го и 3-го уровней
        cursor.execute('''
            INSERT OR IGNORE INTO referral_network (referrer_id, referred_id, level)
            SELECT 
                rn1.referrer_id,
                rn2.referred_id,
                2
            FROM referral_network rn1
            JOIN referral_network rn2 ON rn1.referred_id = rn2.referrer_id
            WHERE rn1.level = 1 AND rn2.level = 1
        ''')
        
        cursor.execute('''
            INSERT OR IGNORE INTO referral_network (referrer_id, referred_id, level)
            SELECT 
                rn1.referrer_id,
                rn3.referred_id,
                3
            FROM referral_network rn1
            JOIN referral_network rn2 ON rn1.referred_id = rn2.referrer_id
            JOIN referral_network rn3 ON rn2.referred_id = rn3.referrer_id
            WHERE rn1.level = 1 AND rn2.level = 1 AND rn3.level = 1
        ''')
        
        # 3. Создаем дополнительные тестовые связи
        print("\n🎯 3. Создание дополнительных тестовых связей...")
        
        # Получаем админов
        cursor.execute("SELECT telegram_id FROM users WHERE telegram_id IN (SELECT telegram_id FROM admins)")
        admins = [row[0] for row in cursor.fetchall()]
        
        # Получаем всех пользователей
        cursor.execute("SELECT telegram_id FROM users")
        all_users = [row[0] for row in cursor.fetchall()]
        
        # Создаем дополнительные связи для админов
        for admin_id in admins:
            # Каждый админ приглашает 5-8 человек
            num_referrals = random.randint(5, 8)
            available_users = [u for u in all_users if u != admin_id]
            referred_users = random.sample(available_users, min(num_referrals, len(available_users)))
            
            for referred_id in referred_users:
                # Проверяем, не приглашен ли уже этот пользователь
                cursor.execute('''
                    SELECT COUNT(*) FROM referral_network 
                    WHERE referred_id = ?
                ''', (referred_id,))
                
                if cursor.fetchone()[0] == 0:  # Если не приглашен
                    cursor.execute('''
                        INSERT OR IGNORE INTO referral_network (referrer_id, referred_id, level)
                        VALUES (?, ?, 1)
                    ''', (admin_id, referred_id))
                    
                    cursor.execute('''
                        UPDATE users SET referrer_id = ? WHERE telegram_id = ?
                    ''', (admin_id, referred_id))
        
        # Пересоздаем связи 2-го и 3-го уровней
        cursor.execute('DELETE FROM referral_network WHERE level > 1')
        
        cursor.execute('''
            INSERT OR IGNORE INTO referral_network (referrer_id, referred_id, level)
            SELECT 
                rn1.referrer_id,
                rn2.referred_id,
                2
            FROM referral_network rn1
            JOIN referral_network rn2 ON rn1.referred_id = rn2.referrer_id
            WHERE rn1.level = 1 AND rn2.level = 1
        ''')
        
        cursor.execute('''
            INSERT OR IGNORE INTO referral_network (referrer_id, referred_id, level)
            SELECT 
                rn1.referrer_id,
                rn3.referred_id,
                3
            FROM referral_network rn1
            JOIN referral_network rn2 ON rn1.referred_id = rn2.referrer_id
            JOIN referral_network rn3 ON rn2.referred_id = rn3.referrer_id
            WHERE rn1.level = 1 AND rn2.level = 1 AND rn3.level = 1
        ''')
        
        # 4. Создаем реферальные балансы для всех пользователей
        print("\n💰 4. Создание реферальных балансов...")
        cursor.execute('''
            INSERT OR IGNORE INTO referral_balances (user_id, balance, total_earned, total_withdrawn)
            SELECT telegram_id, 0.0, 0.0, 0.0 FROM users
        ''')
        
        # 5. Симулируем начисления на основе активных депозитов
        print("\n📊 5. Симуляция начислений на основе активных депозитов...")
        
        # Получаем активные депозиты
        cursor.execute('''
            SELECT d.id, d.user_id, d.amount, d.deposit_type, d.profit_percent
            FROM deposits d
            WHERE d.status = 'active'
        ''')
        active_deposits = cursor.fetchall()
        
        for deposit_id, user_id, amount, deposit_type, profit_percent in active_deposits:
            # Определяем проценты в зависимости от типа депозита
            if deposit_type == '30_days':
                percentages = {1: 15.0, 2: 10.0, 3: 5.0}
            else:  # 10_days
                percentages = {1: 5.0, 2: 3.0, 3: 1.5}
            
            # Находим всех рефереров этого пользователя
            cursor.execute('''
                SELECT referrer_id, level FROM referral_network 
                WHERE referred_id = ?
            ''', (user_id,))
            
            referrers = cursor.fetchall()
            
            for referrer_id, level in referrers:
                if level in percentages:
                    # Рассчитываем сумму вознаграждения
                    reward_amount = amount * (percentages[level] / 100)
                    
                    # Обновляем баланс реферера
                    cursor.execute('''
                        UPDATE referral_balances 
                        SET balance = balance + ?, total_earned = total_earned + ?
                        WHERE user_id = ?
                    ''', (reward_amount, reward_amount, referrer_id))
                    
                    # Создаем запись в истории транзакций
                    cursor.execute('''
                        INSERT INTO referral_transactions 
                        (user_id, amount, transaction_type, source_deposit_id, source_user_id, level, description)
                        VALUES (?, ?, 'earned', ?, ?, ?, ?)
                    ''', (referrer_id, reward_amount, deposit_id, user_id, level, 
                          f"Реферальное вознаграждение {level}-го уровня с депозита #{deposit_id}"))
        
        conn.commit()
        
        # 6. Показываем статистику
        print("\n📊 6. СТАТИСТИКА МИГРАЦИИ:")
        
        cursor.execute('SELECT COUNT(*) FROM referral_network')
        total_connections = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM referral_network WHERE level = 1')
        level1_connections = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM referral_network WHERE level = 2')
        level2_connections = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM referral_network WHERE level = 3')
        level3_connections = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM referral_balances WHERE balance > 0')
        users_with_balance = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(balance) FROM referral_balances')
        total_balance = cursor.fetchone()[0] or 0
        
        print(f"  • Всего связей: {total_connections}")
        print(f"  • 1-й уровень: {level1_connections}")
        print(f"  • 2-й уровень: {level2_connections}")
        print(f"  • 3-й уровень: {level3_connections}")
        print(f"  • Пользователей с балансом: {users_with_balance}")
        print(f"  • Общий баланс: {total_balance:.2f}$")
        
        # 7. Показываем топ рефереров
        print("\n🏆 7. ТОП РЕФЕРЕРОВ ПО БАЛАНСУ:")
        cursor.execute('''
            SELECT u.first_name, rb.balance, rb.total_earned, 
                   COUNT(rn1.id) as level1_count,
                   COUNT(rn2.id) as level2_count,
                   COUNT(rn3.id) as level3_count
            FROM referral_balances rb
            JOIN users u ON rb.user_id = u.telegram_id
            LEFT JOIN referral_network rn1 ON rb.user_id = rn1.referrer_id AND rn1.level = 1
            LEFT JOIN referral_network rn2 ON rb.user_id = rn2.referrer_id AND rn2.level = 2
            LEFT JOIN referral_network rn3 ON rb.user_id = rn3.referrer_id AND rn3.level = 3
            WHERE rb.balance > 0
            GROUP BY rb.user_id, u.first_name, rb.balance, rb.total_earned
            ORDER BY rb.balance DESC
            LIMIT 10
        ''')
        
        for name, balance, total_earned, l1, l2, l3 in cursor.fetchall():
            print(f"  • {name}: {balance:.2f}$ (всего: {total_earned:.2f}$) | Уровни: {l1}/{l2}/{l3}")
        
        print("\n✅ МИГРАЦИЯ ЗАВЕРШЕНА!")
        print("\n🎯 НОВАЯ СИСТЕМА ГОТОВА К РАБОТЕ!")

if __name__ == "__main__":
    migrate_referral_data()






