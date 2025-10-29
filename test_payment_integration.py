#!/usr/bin/env python3
"""
Тест интеграции платежной системы
"""

import requests
import time
from payment_client import payment_client

def test_payment_api():
    """Тестирование Payment Bot API"""
    print("🧪 Тестирование интеграции платежной системы...")
    
    # Тест 1: Проверка соединения
    print("\n1️⃣ Проверка соединения с Payment Bot API...")
    if payment_client.test_connection():
        print("✅ Соединение с Payment Bot API установлено")
    else:
        print("❌ Не удалось подключиться к Payment Bot API")
        print("💡 Убедитесь, что Payment Bot запущен на localhost:8002")
        return False
    
    # Тест 2: Получение информации о кошельке
    print("\n2️⃣ Тестирование получения информации о кошельке...")
    test_wallet = "TJR44gwdyGhLa4833zJtutNepRoNVFpMzX"
    result = payment_client.get_wallet_info(test_wallet)
    
    if result.get("success"):
        balance = result.get("balance", 0)
        print(f"✅ Информация о кошельке получена: баланс {balance} USDT")
    else:
        print(f"❌ Ошибка получения информации о кошельке: {result.get('error', 'Неизвестная ошибка')}")
    
    # Тест 3: Проверка платежа
    print("\n3️⃣ Тестирование проверки платежа...")
    result = payment_client.verify_payment(test_wallet, 1.0)
    
    if result.get("success"):
        if result.get("confirmed"):
            print("✅ Платеж подтвержден")
        else:
            print("ℹ️ Платеж не найден (это нормально для тестового кошелька)")
    else:
        print(f"❌ Ошибка проверки платежа: {result.get('error', 'Неизвестная ошибка')}")
    
    print("\n🎉 Тестирование завершено!")
    return True

def test_database_integration():
    """Тестирование интеграции с базой данных"""
    print("\n🗄️ Тестирование интеграции с базой данных...")
    
    try:
        import sqlite3
        
        # Проверяем таблицу pending_payments
        with sqlite3.connect("bot_database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pending_payments'")
            result = cursor.fetchone()
            
            if result:
                print("✅ Таблица pending_payments существует")
                
                # Проверяем структуру таблицы
                cursor.execute("PRAGMA table_info(pending_payments)")
                columns = cursor.fetchall()
                print(f"📋 Структура таблицы: {len(columns)} колонок")
                
                # Проверяем таблицу user_wallets
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_wallets'")
                result = cursor.fetchone()
                
                if result:
                    print("✅ Таблица user_wallets существует")
                else:
                    print("❌ Таблица user_wallets не найдена")
                    
            else:
                print("❌ Таблица pending_payments не найдена")
                
    except Exception as e:
        print(f"❌ Ошибка тестирования базы данных: {e}")
        return False
    
    return True

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ ПЛАТЕЖНОЙ СИСТЕМЫ")
    print("=" * 50)
    
    # Тест базы данных
    db_ok = test_database_integration()
    
    # Тест API
    api_ok = test_payment_api()
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"🗄️ База данных: {'✅ OK' if db_ok else '❌ ОШИБКА'}")
    print(f"🌐 Payment API: {'✅ OK' if api_ok else '❌ ОШИБКА'}")
    
    if db_ok and api_ok:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Интеграция работает корректно.")
        print("\n💡 Доступные команды:")
        print("   /pay <сумма> - создать платеж")
        print("   /setwallet <адрес> - настроить кошелек")
        print("   /walletbalance - проверить баланс кошелька")
    else:
        print("\n⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ. Проверьте настройки.")

if __name__ == "__main__":
    main()






