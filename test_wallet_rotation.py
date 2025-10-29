#!/usr/bin/env python3
"""
Тест ротации кошельков для проверки работы Payment Bot
Меняет кошелек каждые 20 секунд между двумя вариантами
"""

import time
import requests
import json
from datetime import datetime

# Конфигурация
PAYMENT_API_URL = "http://localhost:8002"
PAYMENT_API_KEY = "rsG7Hzt0EaEY5ZoEH4eE96SiY234qpiSYg5d92xrSm4"

# Два кошелька для тестирования
WALLET_1 = "TWJ5wQPnJTk2keYXjEgf19i17ZzACBY4Mx"
WALLET_2 = "TRpxhgJ9izoZ56iHJ6gkWwvuStaMeCTisS"

def test_payment_bot_connection():
    """Проверяем соединение с Payment Bot"""
    try:
        response = requests.get(
            f"{PAYMENT_API_URL}/health",
            headers={"X-API-Key": PAYMENT_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Payment Bot доступен")
            return True
        else:
            print(f"❌ Payment Bot недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка соединения с Payment Bot: {e}")
        return False

def get_current_wallet():
    """Получаем текущий кошелек из Payment Bot"""
    try:
        response = requests.get(
            f"{PAYMENT_API_URL}/wallet-info",
            headers={"X-API-Key": PAYMENT_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("wallet_address", "Неизвестно")
            else:
                return "Ошибка получения"
        else:
            return f"HTTP {response.status_code}"
    except Exception as e:
        return f"Ошибка: {e}"

def test_our_bot():
    """Тестируем наш бот"""
    try:
        from payment_client import payment_client
        result = payment_client.get_payment_wallet("TJR44gwdyGhLa4833zJtutNepRoNVFpMzX")
        if result.get("success"):
            return result.get("wallet_address", "Неизвестно")
        else:
            return f"Ошибка: {result.get('error', 'Неизвестная ошибка')}"
    except Exception as e:
        return f"Ошибка: {e}"

def main():
    print("🚀 ЗАПУСК ТЕСТА РОТАЦИИ КОШЕЛЬКОВ")
    print("=" * 60)
    print(f"📅 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Интервал смены: 20 секунд")
    print(f"🔄 Общее время теста: 200 секунд")
    print(f"💰 Кошелек 1: {WALLET_1}")
    print(f"💰 Кошелек 2: {WALLET_2}")
    print()
    
    # Проверяем соединение с Payment Bot
    if not test_payment_bot_connection():
        print("❌ Payment Bot недоступен. Тест невозможен.")
        return
    
    print("🔄 НАЧИНАЕМ ТЕСТ...")
    print()
    
    current_wallet = WALLET_1
    test_duration = 200  # 200 секунд
    interval = 20  # 20 секунд
    
    for cycle in range(test_duration // interval):
        print(f"🔄 ЦИКЛ {cycle + 1}/10 - {datetime.now().strftime('%H:%M:%S')}")
        print(f"📤 Устанавливаем кошелек: {current_wallet}")
        
        # Здесь должен быть код для смены кошелька в Payment Bot
        # Пока что просто выводим информацию
        
        print("📊 ПРОВЕРЯЕМ РЕЗУЛЬТАТЫ:")
        
        # Проверяем Payment Bot напрямую
        payment_bot_wallet = get_current_wallet()
        print(f"  🤖 Payment Bot: {payment_bot_wallet}")
        
        # Проверяем наш бот
        our_bot_wallet = test_our_bot()
        print(f"  🎯 Наш бот: {our_bot_wallet}")
        
        # Проверяем соответствие
        if payment_bot_wallet == current_wallet:
            print("  ✅ Payment Bot показывает правильный кошелек")
        else:
            print("  ❌ Payment Bot показывает неправильный кошелек")
        
        if our_bot_wallet == current_wallet:
            print("  ✅ Наш бот показывает правильный кошелек")
        else:
            print("  ❌ Наш бот показывает неправильный кошелек")
        
        print()
        
        # Меняем кошелек для следующего цикла
        current_wallet = WALLET_2 if current_wallet == WALLET_1 else WALLET_1
        
        # Ждем до следующего цикла
        if cycle < (test_duration // interval) - 1:
            print(f"⏳ Ждем {interval} секунд до следующего цикла...")
            time.sleep(interval)
    
    print("🏁 ТЕСТ ЗАВЕРШЕН!")
    print(f"📅 Время окончания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()





