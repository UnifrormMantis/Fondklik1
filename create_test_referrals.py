#!/usr/bin/env python3
"""
Скрипт для создания тестовых реферальных данных
"""

import sqlite3
import random
from datetime import datetime, timedelta

DATABASE_PATH = "bot_database.db"

def create_test_referrals():
    """Создать тестовые реферальные данные"""
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Получаем существующих пользователей
        cursor.execute("SELECT telegram_id, first_name FROM users LIMIT 10")
        users = cursor.fetchall()
        
        if len(users) < 2:
            print("❌ Недостаточно пользователей для создания рефералов")
            return
        
        print(f"📊 Найдено {len(users)} пользователей")
        
        # Создаем реферальные записи
        referral_data = []
        
        # Создаем 20 реферальных записей
        for i in range(20):
            # Выбираем случайного реферера и реферала
            referrer = random.choice(users)
            referred = random.choice([u for u in users if u[0] != referrer[0]])
            
            # Случайные параметры
            level = random.choice([1, 2])  # 1-й или 2-й уровень
            amount = round(random.uniform(50, 500), 2)  # Сумма от 50 до 500
            percentage = 5.0 if level == 1 else 2.0  # 5% для 1-го уровня, 2% для 2-го
            
            # Случайная дата в последние 30 дней
            days_ago = random.randint(0, 30)
            created_at = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Случайно определяем, есть ли транзакция (выплачено или нет)
            transaction_id = random.randint(1, 100) if random.choice([True, False]) else None
            
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
        
        print(f"✅ Создано {len(referral_data)} реферальных записей")
        
        # Показываем статистику
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
📊 СТАТИСТИКА РЕФЕРАЛОВ:
• Всего записей: {stats[0]}
• Выплачено: {stats[1]}
• Ожидает выплаты: {stats[2]}
• Общая сумма: {stats[3]:.2f}$
• Средняя сумма: {stats[4]:.2f}$
        """)

if __name__ == "__main__":
    create_test_referrals()






