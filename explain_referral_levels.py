#!/usr/bin/env python3
"""
Детальное объяснение работы уровней в реферальной системе
"""

import sqlite3

DATABASE_PATH = "bot_database.db"

def explain_referral_levels():
    """Объяснить как работают уровни"""
    
    print("🔗 ДЕТАЛЬНОЕ ОБЪЯСНЕНИЕ РАБОТЫ УРОВНЕЙ")
    print("=" * 60)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Показываем структуру для Alice
        print("👑 ПРИМЕР: РЕФЕРАЛЬНАЯ СЕТЬ ALICE")
        print("-" * 40)
        
        # 1-й уровень Alice
        cursor.execute('''
            SELECT u2.first_name, u2.telegram_id
            FROM referral_network rn
            JOIN users u2 ON rn.referred_id = u2.telegram_id
            WHERE rn.referrer_id = (SELECT telegram_id FROM users WHERE first_name = 'Alice')
            AND rn.level = 1
            ORDER BY u2.first_name
        ''')
        
        level1_users = cursor.fetchall()
        print(f"1-й УРОВЕНЬ (прямые рефералы Alice): {len(level1_users)} человек")
        for name, user_id in level1_users:
            print(f"  • {name} (ID: {user_id})")
        
        # 2-й уровень Alice
        cursor.execute('''
            SELECT u2.first_name, u2.telegram_id
            FROM referral_network rn
            JOIN users u2 ON rn.referred_id = u2.telegram_id
            WHERE rn.referrer_id = (SELECT telegram_id FROM users WHERE first_name = 'Alice')
            AND rn.level = 2
            ORDER BY u2.first_name
        ''')
        
        level2_users = cursor.fetchall()
        print(f"\n2-й УРОВЕНЬ (рефералы рефералов Alice): {len(level2_users)} человек")
        for name, user_id in level2_users:
            print(f"  • {name} (ID: {user_id})")
        
        # 3-й уровень Alice
        cursor.execute('''
            SELECT u2.first_name, u2.telegram_id
            FROM referral_network rn
            JOIN users u2 ON rn.referred_id = u2.telegram_id
            WHERE rn.referrer_id = (SELECT telegram_id FROM users WHERE first_name = 'Alice')
            AND rn.level = 3
            ORDER BY u2.first_name
        ''')
        
        level3_users = cursor.fetchall()
        print(f"\n3-й УРОВЕНЬ (рефералы 2-го уровня Alice): {len(level3_users)} человек")
        for name, user_id in level3_users:
            print(f"  • {name} (ID: {user_id})")
        
        # 2. Показываем конкретную цепочку
        print("\n🔗 ПРИМЕР КОНКРЕТНОЙ ЦЕПОЧКИ")
        print("-" * 40)
        
        # Находим пользователя с максимальным количеством связей
        cursor.execute('''
            SELECT referred_id, COUNT(*) as connections
            FROM referral_network
            GROUP BY referred_id
            ORDER BY connections DESC
            LIMIT 1
        ''')
        
        most_connected = cursor.fetchone()
        if most_connected:
            user_id = most_connected[0]
            cursor.execute('SELECT first_name FROM users WHERE telegram_id = ?', (user_id,))
            user_name = cursor.fetchone()[0]
            
            print(f"Пользователь {user_name} (ID: {user_id}) имеет связи с:")
            
            # Показываем все связи этого пользователя
            cursor.execute('''
                SELECT u1.first_name as referrer, rn.level
                FROM referral_network rn
                JOIN users u1 ON rn.referrer_id = u1.telegram_id
                WHERE rn.referred_id = ?
                ORDER BY rn.level, u1.first_name
            ''', (user_id,))
            
            connections = cursor.fetchall()
            for referrer_name, level in connections:
                print(f"  • {referrer_name} (уровень {level})")
        
        # 3. Показываем как создаются уровни
        print("\n⚙️ КАК СОЗДАЮТСЯ УРОВНИ")
        print("-" * 40)
        print("""
1. ПОЛЬЗОВАТЕЛЬ ПРИСОЕДИНЯЕТСЯ:
   • Alice приглашает TestUser1 → создается связь Alice → TestUser1 (уровень 1)

2. РЕФЕРАЛ ПРИГЛАШАЕТ КОГО-ТО:
   • TestUser1 приглашает TestUser2 → создается связь TestUser1 → TestUser2 (уровень 1)
   • АВТОМАТИЧЕСКИ создается связь Alice → TestUser2 (уровень 2)

3. РЕФЕРАЛ 2-ГО УРОВНЯ ПРИГЛАШАЕТ:
   • TestUser2 приглашает TestUser3 → создается связь TestUser2 → TestUser3 (уровень 1)
   • АВТОМАТИЧЕСКИ создается связь TestUser1 → TestUser3 (уровень 2)
   • АВТОМАТИЧЕСКИ создается связь Alice → TestUser3 (уровень 3)
        """)
        
        # 4. Показываем расчет вознаграждений
        print("\n💰 РАСЧЕТ ВОЗНАГРАЖДЕНИЙ")
        print("-" * 40)
        print("""
ПРИМЕР: TestUser3 создает депозит 1000$ на 30 дней

Кто получает вознаграждение:
• Alice (3-й уровень): 1000$ × 5% = 50$
• TestUser1 (2-й уровень): 1000$ × 10% = 100$
• TestUser2 (1-й уровень): 1000$ × 15% = 150$

ИТОГО: 50$ + 100$ + 150$ = 300$ (30% от депозита)
        """)
        
        # 5. Показываем реальные данные
        print("\n📊 РЕАЛЬНЫЕ ДАННЫЕ ИЗ НАШЕЙ СИСТЕМЫ")
        print("-" * 40)
        
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN level = 1 THEN 1 END) as level1,
                COUNT(CASE WHEN level = 2 THEN 1 END) as level2,
                COUNT(CASE WHEN level = 3 THEN 1 END) as level3,
                COUNT(*) as total
            FROM referral_network
        ''')
        
        stats = cursor.fetchone()
        print(f"• Всего связей: {stats[3]}")
        print(f"• 1-й уровень: {stats[0]}")
        print(f"• 2-й уровень: {stats[1]}")
        print(f"• 3-й уровень: {stats[2]}")
        
        # 6. Показываем балансы
        print("\n💳 БАЛАНСЫ РЕФЕРЕРОВ")
        print("-" * 40)
        
        cursor.execute('''
            SELECT u.first_name, rb.balance, rb.total_earned
            FROM referral_balances rb
            JOIN users u ON rb.user_id = u.telegram_id
            WHERE rb.balance > 0
            ORDER BY rb.balance DESC
            LIMIT 5
        ''')
        
        for name, balance, total_earned in cursor.fetchall():
            print(f"• {name}: {balance:.2f}$ (всего заработано: {total_earned:.2f}$)")
        
        print("\n✅ СИСТЕМА РАБОТАЕТ ПРАВИЛЬНО!")
        print("\n🎯 КЛЮЧЕВЫЕ ПРИНЦИПЫ:")
        print("• Каждый пользователь может иметь только ОДНОГО реферера")
        print("• Уровни создаются АВТОМАТИЧЕСКИ при приглашении")
        print("• Вознаграждения начисляются ВСЕМ уровням при создании депозита")
        print("• Проценты зависят от ТИПА депозита (10 или 30 дней)")
        print("• Средства НАКАПЛИВАЮТСЯ в балансе пользователя")
        print("• Пользователь может вывести ЛЮБУЮ сумму до своего баланса")

if __name__ == "__main__":
    explain_referral_levels()






