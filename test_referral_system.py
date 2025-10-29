#!/usr/bin/env python3
"""
Скрипт для тестирования реферальной системы
"""

import sqlite3
from datetime import datetime, timedelta

DATABASE_PATH = "bot_database.db"

def test_referral_system():
    """Тестировать реферальную систему"""
    
    print("🧪 ТЕСТИРОВАНИЕ РЕФЕРАЛЬНОЙ СИСТЕМЫ")
    print("=" * 50)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Общая статистика
        print("\n📊 1. ОБЩАЯ СТАТИСТИКА:")
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
        print(f"• Всего записей: {stats[0]}")
        print(f"• Выплачено: {stats[1]}")
        print(f"• Ожидает выплаты: {stats[2]}")
        print(f"• Общая сумма: {stats[3]:.2f}$")
        print(f"• Средняя сумма: {stats[4]:.2f}$")
        
        # 2. Статистика по уровням
        print("\n🎯 2. СТАТИСТИКА ПО УРОВНЯМ:")
        cursor.execute('''
            SELECT 
                level,
                COUNT(*) as count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount
            FROM referral_payments
            GROUP BY level
            ORDER BY level
        ''')
        
        for level, count, total, avg in cursor.fetchall():
            print(f"• Уровень {level}: {count} записей, {total:.2f}$ (среднее: {avg:.2f}$)")
        
        # 3. Статистика по дням (последние 7 дней)
        print("\n📅 3. СТАТИСТИКА ПО ДНЯМ (последние 7 дней):")
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            date_short = (datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y')
            
            # Выплаченные рефералы за день
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                FROM referral_payments 
                WHERE DATE(created_at) = ? AND transaction_id IS NOT NULL
            ''', (date,))
            paid_count, paid_sum = cursor.fetchone()
            
            # Ожидающие выплаты за день
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                FROM referral_payments 
                WHERE DATE(created_at) = ? AND transaction_id IS NULL
            ''', (date,))
            pending_count, pending_sum = cursor.fetchone()
            
            if paid_count > 0 or pending_count > 0:
                print(f"• {date_short}: выплачено {paid_count}/{paid_sum:.0f}$, ожидает {pending_count}/{pending_sum:.0f}$")
        
        # 4. Топ рефереров
        print("\n👑 4. ТОП РЕФЕРЕРОВ:")
        cursor.execute('''
            SELECT 
                u.first_name,
                COUNT(rp.id) as referrals_count,
                SUM(rp.amount) as total_amount,
                COUNT(CASE WHEN rp.transaction_id IS NOT NULL THEN 1 END) as paid_count
            FROM referral_payments rp
            JOIN users u ON rp.referrer_id = u.telegram_id
            GROUP BY rp.referrer_id, u.first_name
            ORDER BY referrals_count DESC
            LIMIT 5
        ''')
        
        for name, count, total, paid in cursor.fetchall():
            print(f"• {name}: {count} рефералов, {total:.2f}$ (выплачено: {paid})")
        
        # 5. Ожидающие выплаты (первые 3)
        print("\n⏳ 5. ОЖИДАЮЩИЕ ВЫПЛАТЫ (первые 3):")
        cursor.execute('''
            SELECT rp.id, rp.amount, rp.created_at, rp.level, 
                   u1.first_name as referrer_name, u2.first_name as referred_name
            FROM referral_payments rp
            JOIN users u1 ON rp.referrer_id = u1.telegram_id
            JOIN users u2 ON rp.referred_id = u2.telegram_id
            WHERE rp.transaction_id IS NULL
            ORDER BY rp.created_at ASC
            LIMIT 3
        ''')
        
        for ref_id, amount, created_at, level, referrer, referred in cursor.fetchall():
            print(f"• #{ref_id}: {referrer} → {referred}, {amount:.2f}$ (уровень {level}), {created_at[:16]}")
        
        # 6. Тест SQL запросов из бота
        print("\n🔍 6. ТЕСТ SQL ЗАПРОСОВ ИЗ БОТА:")
        
        # Тест запроса для show_admin_referral_payments
        print("• Тест статистики по дням (30 дней):")
        daily_stats = []
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                FROM referral_payments 
                WHERE DATE(created_at) = ? AND transaction_id IS NOT NULL
            ''', (date,))
            paid_count, paid_sum = cursor.fetchone()
            if paid_count > 0:
                daily_stats.append((date, paid_count, paid_sum))
        
        print(f"  Найдено {len(daily_stats)} дней с выплатами")
        
        # Тест запроса для show_admin_pending_referral_payments
        print("• Тест запроса ожидающих выплат:")
        cursor.execute('''
            SELECT rp.id, rp.amount, rp.created_at, rp.level, 
                   u1.first_name as referrer_name, u1.username as referrer_username, u1.wallet_address as referrer_wallet,
                   u2.first_name as referred_name, u2.username as referred_username
            FROM referral_payments rp
            JOIN users u1 ON rp.referrer_id = u1.telegram_id
            JOIN users u2 ON rp.referred_id = u2.telegram_id
            WHERE rp.transaction_id IS NULL
            ORDER BY rp.created_at ASC
            LIMIT 1
        ''')
        
        referral = cursor.fetchone()
        if referral:
            print(f"  Первая ожидающая выплата: #{referral[0]}, {referral[1]:.2f}$")
        else:
            print("  Нет ожидающих выплат")
        
        print("\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")

if __name__ == "__main__":
    test_referral_system()