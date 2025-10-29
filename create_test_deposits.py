#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import random
from datetime import datetime, timedelta
import os

# Путь к базе данных
DATABASE_PATH = "bot_database.db"

def create_test_deposits():
    """Создать 100 тестовых вкладов"""
    
    # Список тестовых пользователей
    test_users = [
        (798427688, "Admin", "admin_user"),
        (123456789, "TestUser1", "test1"),
        (234567890, "TestUser2", "test2"),
        (345678901, "TestUser3", "test3"),
        (456789012, "TestUser4", "test4"),
        (567890123, "TestUser5", "test5"),
        (678901234, "TestUser6", "test6"),
        (789012345, "TestUser7", "test7"),
        (890123456, "TestUser8", "test8"),
        (901234567, "TestUser9", "test9"),
        (112233445, "TestUser10", "test10"),
        (223344556, "TestUser11", "test11"),
        (334455667, "TestUser12", "test12"),
        (445566778, "TestUser13", "test13"),
        (556677889, "TestUser14", "test14"),
        (667788990, "TestUser15", "test15"),
        (778899001, "TestUser16", "test16"),
        (889900112, "TestUser17", "test17"),
        (990011223, "TestUser18", "test18"),
        (101112131, "TestUser19", "test19"),
        (202122232, "TestUser20", "test20")
    ]
    
    # Суммы вкладов
    amounts = [10, 25, 50, 100, 150, 200, 250, 300, 400, 500, 750, 1000, 1500, 2000, 2500, 3000, 5000, 7500, 10000]
    
    # Типы вкладов
    deposit_types = ['10_days', '30_days']
    
    # Проценты прибыли
    profit_percents = [10, 30]
    
    # Статусы
    statuses = ['pending', 'completed', 'active']
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            print("🔄 Создание тестовых пользователей...")
            
            # Создаем тестовых пользователей
            for user_id, first_name, username in test_users:
                cursor.execute('''
                    INSERT OR IGNORE INTO users (telegram_id, username, first_name, wallet_address, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, first_name, f"TEST_WALLET_{user_id}", datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            print("🔄 Создание тестовых вкладов...")
            
            # Создаем 100 тестовых вкладов
            for i in range(100):
                # Случайный пользователь
                user_id, first_name, username = random.choice(test_users)
                
                # Случайная сумма
                amount = random.choice(amounts)
                
                # Случайный тип вклада
                deposit_type = random.choice(deposit_types)
                
                # Процент прибыли в зависимости от типа
                profit_percent = 8 if deposit_type == '10_days' else 30
                
                # Случайный статус
                status = random.choice(statuses)
                
                # Случайная дата (последние 30 дней)
                days_ago = random.randint(0, 30)
                created_at = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
                
                # Дата истечения
                duration_days = 10 if deposit_type == '10_days' else 30
                expires_at = (datetime.now() - timedelta(days=days_ago) + timedelta(days=duration_days)).strftime('%Y-%m-%d %H:%M:%S')
                
                # Создаем вклад
                cursor.execute('''
                    INSERT INTO deposits (user_id, amount, deposit_type, profit_percent, status, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, amount, deposit_type, profit_percent, status, created_at, expires_at))
                
                print(f"✅ Создан вклад #{i+1}: {amount} USDT на {duration_days} дней ({profit_percent}%), статус: {status}, пользователь: {first_name}")
            
            conn.commit()
            
            # Статистика
            cursor.execute('SELECT COUNT(*) FROM deposits')
            total_deposits = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM deposits WHERE status = "pending"')
            pending_deposits = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM deposits WHERE status = "completed"')
            completed_deposits = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM deposits WHERE status = "active"')
            active_deposits = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(amount) FROM deposits')
            total_amount = cursor.fetchone()[0] or 0
            
            print(f"\n📊 СТАТИСТИКА:")
            print(f"• Всего вкладов: {total_deposits}")
            print(f"• Ожидающих выплаты (pending): {pending_deposits}")
            print(f"• Завершенных (completed): {completed_deposits}")
            print(f"• Активных (active): {active_deposits}")
            print(f"• Общая сумма: {total_amount:.2f} USDT")
            
            # Статистика по дням
            print(f"\n📅 СТАТИСТИКА ПО ДНЯМ (последние 7 дней):")
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                date_short = (datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y')
                
                cursor.execute('''
                    SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                    FROM deposits 
                    WHERE DATE(created_at) = ? AND status = 'pending'
                ''', (date,))
                pending_count, pending_sum = cursor.fetchone()
                
                cursor.execute('''
                    SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                    FROM deposits 
                    WHERE DATE(created_at) = ? AND status = 'completed'
                ''', (date,))
                completed_count, completed_sum = cursor.fetchone()
                
                if pending_count > 0 or completed_count > 0:
                    print(f"{date_short}: pending {pending_count}/{pending_sum:.0f}$ | completed {completed_count}/{completed_sum:.0f}$")
            
            print(f"\n✅ Успешно создано 100 тестовых вкладов!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    create_test_deposits()