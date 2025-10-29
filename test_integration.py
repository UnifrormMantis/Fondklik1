#!/usr/bin/env python3
"""
Тест интеграции Payment Bot с основным ботом
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from payment_client_integration import PaymentClient
import sqlite3

def test_payment_client():
    """Тест PaymentClient"""
    print("🧪 Тестирование PaymentClient...")
    
    client = PaymentClient('rsG7Hzt0EaEY5ZoEH4eE96SiY234qpiSYg5d92xrSm4', 'http://localhost:8001')
    
    # Тест получения кошелька
    result = client.get_payment_wallet('TTestUserWallet123456789')
    print(f"✅ get_payment_wallet: {result}")
    
    # Тест проверки платежей
    result = client.check_user_payments('TTestUserWallet123456789')
    print(f"✅ check_user_payments: {result}")

def test_database():
    """Тест базы данных"""
    print("\n🧪 Тестирование базы данных...")
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    # Проверяем структуру таблицы users
    cursor.execute("PRAGMA table_info(users);")
    columns = cursor.fetchall()
    print(f"✅ Структура таблицы users: {len(columns)} колонок")
    
    # Проверяем наличие поля wallet_address
    wallet_address_exists = any(col[1] == 'wallet_address' for col in columns)
    print(f"✅ Поле wallet_address: {'найдено' if wallet_address_exists else 'НЕ найдено'}")
    
    # Проверяем таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"✅ Таблицы в базе данных: {len(tables)}")
    
    conn.close()

def test_bot_import():
    """Тест импорта основного бота"""
    print("\n🧪 Тестирование импорта основного бота...")
    
    try:
        from bot_final import CryptoBot
        print("✅ Импорт CryptoBot успешен")
        
        # Проверяем наличие новых методов
        methods = ['wallet_command', 'pay_command', 'balance_command', 'check_payment_callback']
        
        for method in methods:
            if hasattr(CryptoBot, method):
                print(f"✅ Метод {method} найден")
            else:
                print(f"❌ Метод {method} НЕ найден")
        
        # Проверяем наличие PaymentClient в __init__
        import inspect
        init_source = inspect.getsource(CryptoBot.__init__)
        if 'payment_client' in init_source:
            print("✅ PaymentClient инициализирован")
        else:
            print("❌ PaymentClient НЕ инициализирован")
            
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")

if __name__ == "__main__":
    print("🚀 Тестирование интеграции Payment Bot...")
    print("=" * 50)
    
    test_payment_client()
    test_database()
    test_bot_import()
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")
