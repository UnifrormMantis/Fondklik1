#!/usr/bin/env python3
"""
Обновление реферальной системы на 3-уровневую с правильной логикой
"""

import sqlite3
from datetime import datetime

DATABASE_PATH = "bot_database.db"

def update_referral_system():
    """Обновить реферальную систему"""
    
    print("🔄 ОБНОВЛЕНИЕ РЕФЕРАЛЬНОЙ СИСТЕМЫ")
    print("=" * 50)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Создаем новую таблицу для реферальных связей
        print("📋 1. Создание таблицы реферальных связей...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_network (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                level INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(referrer_id, referred_id),
                FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                FOREIGN KEY (referred_id) REFERENCES users (telegram_id)
            )
        ''')
        
        # 2. Создаем таблицу для реферальных балансов
        print("💰 2. Создание таблицы реферальных балансов...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                balance REAL DEFAULT 0.0,
                total_earned REAL DEFAULT 0.0,
                total_withdrawn REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id),
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        ''')
        
        # 3. Создаем таблицу для реферальных транзакций
        print("📊 3. Создание таблицы реферальных транзакций...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL, -- 'earned' или 'withdrawn'
                source_deposit_id INTEGER,
                source_user_id INTEGER,
                level INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                FOREIGN KEY (source_deposit_id) REFERENCES deposits (id),
                FOREIGN KEY (source_user_id) REFERENCES users (telegram_id)
            )
        ''')
        
        # 4. Создаем таблицу для реферальных выводов
        print("💸 4. Создание таблицы реферальных выводов...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending', -- 'pending', 'completed', 'rejected'
                wallet_address TEXT,
                transaction_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        ''')
        
        # 5. Добавляем колонку referrer_id в таблицу users
        print("👥 5. Добавление referrer_id в таблицу users...")
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN referrer_id INTEGER')
            cursor.execute('ALTER TABLE users ADD COLUMN referral_code TEXT')
        except sqlite3.OperationalError:
            print("  Колонки уже существуют")
        
        # 6. Создаем индексы для оптимизации
        print("⚡ 6. Создание индексов...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_referral_network_referrer ON referral_network(referrer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_referral_network_referred ON referral_network(referred_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_referral_network_level ON referral_network(level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_referral_balances_user ON referral_balances(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_referral_transactions_user ON referral_transactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_referral_withdrawals_user ON referral_withdrawals(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_referrer ON users(referrer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)')
        
        conn.commit()
        
        print("✅ Структура базы данных обновлена!")
        
        # 7. Показываем новую структуру
        print("\n📋 НОВАЯ СТРУКТУРА РЕФЕРАЛЬНОЙ СИСТЕМЫ:")
        print("""
🔗 referral_network - связи между пользователями
   • referrer_id - кто пригласил
   • referred_id - кого пригласили  
   • level - уровень связи (1, 2, 3)

💰 referral_balances - балансы пользователей
   • user_id - пользователь
   • balance - текущий баланс
   • total_earned - всего заработано
   • total_withdrawn - всего выведено

📊 referral_transactions - история операций
   • user_id - пользователь
   • amount - сумма
   • transaction_type - 'earned' или 'withdrawn'
   • source_deposit_id - источник дохода
   • level - уровень реферала

💸 referral_withdrawals - заявки на вывод
   • user_id - пользователь
   • amount - сумма вывода
   • status - статус заявки
   • wallet_address - кошелек для вывода

👥 users - обновленная таблица пользователей
   • referrer_id - кто пригласил этого пользователя
   • referral_code - уникальный реферальный код
        """)
        
        # 8. Показываем проценты по уровням
        print("\n💰 ПРОЦЕНТЫ ПО УРОВНЯМ:")
        print("""
📅 30-дневные депозиты:
   • 1-й уровень: 15%
   • 2-й уровень: 10%  
   • 3-й уровень: 5%

📅 10-дневные депозиты:
   • 1-й уровень: 5%
   • 2-й уровень: 3%
   • 3-й уровень: 1.5%
        """)
        
        print("\n🎯 ЛОГИКА РАБОТЫ:")
        print("""
1. Пользователь получает уникальную реферальную ссылку
2. При приглашении создается связь в referral_network
3. При создании депозита начисляется вознаграждение всем уровням
4. Вознаграждения накапливаются в referral_balances
5. Пользователь может вывести любую сумму до своего баланса
6. При выводе создается заявка в referral_withdrawals
7. Админ обрабатывает заявку и создает транзакцию
        """)

if __name__ == "__main__":
    update_referral_system()






