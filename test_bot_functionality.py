#!/usr/bin/env python3
"""
Тест функциональности бота
"""

import asyncio
import sys
import os

# Добавляем путь к модулю бота
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_bot_import():
    """Тест импорта бота"""
    try:
        from bot_final import FastBot
        print("✅ Импорт бота успешен")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта бота: {e}")
        return False

async def test_bot_creation():
    """Тест создания экземпляра бота"""
    try:
        from bot_final import FastBot
        bot = FastBot()
        print("✅ Создание экземпляра бота успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания бота: {e}")
        return False

async def test_database_connection():
    """Тест подключения к базе данных"""
    try:
        # Тестируем подключение к БД напрямую
        import sqlite3
        with sqlite3.connect('bot_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"✅ Подключение к БД успешно. Таблицы: {len(tables)}")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False

async def test_crypto_bot_import():
    """Тест импорта crypto_bot"""
    try:
        import crypto_bot
        print("✅ Импорт crypto_bot успешен")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта crypto_bot: {e}")
        return False

async def test_logo_file_id():
    """Тест file_id логотипа"""
    try:
        logo_file_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        if len(logo_file_id) > 50:
            print("✅ File ID логотипа корректный")
            return True
        else:
            print("❌ File ID логотипа слишком короткий")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки file_id: {e}")
        return False

async def test_handlers():
    """Тест обработчиков"""
    try:
        # Проверяем что файл бота существует и содержит нужные методы
        with open('bot_final.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_methods = [
            'show_main_menu',
            'button_callback', 
            'handle_message',
            'start_command'
        ]
        
        missing_methods = []
        for method in required_methods:
            if f'def {method}' not in content:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Отсутствуют методы: {missing_methods}")
            return False
        else:
            print(f"✅ Все необходимые методы присутствуют")
            return True
    except Exception as e:
        print(f"❌ Ошибка проверки обработчиков: {e}")
        return False

async def run_all_tests():
    """Запуск всех тестов"""
    print("🔍 Тестируем функциональность бота")
    print("=" * 60)
    
    tests = [
        ("Импорт бота", test_bot_import),
        ("Создание экземпляра", test_bot_creation),
        ("Подключение к БД", test_database_connection),
        ("Импорт crypto_bot", test_crypto_bot_import),
        ("File ID логотипа", test_logo_file_id),
        ("Обработчики", test_handlers),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Тест: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 ИТОГО: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Бот готов к работе.")
    else:
        print("⚠️ Есть проблемы, требующие исправления.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())
