#!/usr/bin/env python3
"""
Простой тест кошельков для проверки работы системы
"""

import time
from datetime import datetime
from payment_client import payment_client

def test_bot_wallet():
    """Тестируем, какой кошелек возвращает наш бот"""
    try:
        result = payment_client.get_payment_wallet("TJR44gwdyGhLa4833zJtutNepRoNVFpMzX")
        if result.get("success"):
            return result.get("wallet_address", "Неизвестно")
        else:
            return f"Ошибка: {result.get('error', 'Неизвестная ошибка')}"
    except Exception as e:
        return f"Ошибка: {e}"

def main():
    print("🚀 ПРОСТОЙ ТЕСТ КОШЕЛЬКОВ")
    print("=" * 50)
    print(f"📅 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Интервал проверки: 20 секунд")
    print(f"🔄 Общее время теста: 200 секунд")
    print()
    
    print("🔍 НАЧИНАЕМ ТЕСТ...")
    print()
    
    test_duration = 200  # 200 секунд
    interval = 20  # 20 секунд
    
    for cycle in range(test_duration // interval):
        print(f"🔄 ЦИКЛ {cycle + 1}/10 - {datetime.now().strftime('%H:%M:%S')}")
        
        # Проверяем, что возвращает наш бот
        our_bot_wallet = test_bot_wallet()
        print(f"🎯 Наш бот возвращает: {our_bot_wallet}")
        
        # Проверяем соединение с Payment Bot
        if payment_client.test_connection():
            print("  ✅ Соединение с Payment Bot установлено")
        else:
            print("  ❌ Соединение с Payment Bot не установлено")
            print("  💡 Бот использует fallback кошелек")
        
        print()
        
        # Ждем до следующего цикла
        if cycle < (test_duration // interval) - 1:
            print(f"⏳ Ждем {interval} секунд до следующего цикла...")
            time.sleep(interval)
    
    print("🏁 ТЕСТ ЗАВЕРШЕН!")
    print(f"📅 Время окончания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()





