#!/usr/bin/env python3
"""
Тест реакции нашего бота на изменения кошельков
"""

import time
from datetime import datetime
from payment_client import payment_client

# Два кошелька для тестирования
WALLET_1 = "TWJ5wQPnJTk2keYXjEgf19i17ZzACBY4Mx"
WALLET_2 = "TRpxhgJ9izoZ56iHJ6gkWwvuStaMeCTisS"

def test_our_bot():
    """Тестируем наш бот"""
    try:
        result = payment_client.get_payment_wallet("TJR44gwdyGhLa4833zJtutNepRoNVFpMzX")
        if result.get("success"):
            return result.get("wallet_address", "Неизвестно")
        else:
            return f"Ошибка: {result.get('error', 'Неизвестная ошибка')}"
    except Exception as e:
        return f"Ошибка: {e}"

def simulate_wallet_change():
    """Симулируем смену кошелька в payment_client"""
    global payment_client
    
    # Меняем кошелек в payment_client
    if hasattr(payment_client, 'current_wallet'):
        payment_client.current_wallet = WALLET_2 if payment_client.current_wallet == WALLET_1 else WALLET_1
    else:
        payment_client.current_wallet = WALLET_1
    
    return payment_client.current_wallet

def main():
    print("🚀 ТЕСТ РЕАКЦИИ НАШЕГО БОТА НА ИЗМЕНЕНИЯ КОШЕЛЬКОВ")
    print("=" * 70)
    print(f"📅 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Интервал проверки: 20 секунд")
    print(f"🔄 Общее время теста: 200 секунд")
    print(f"💰 Кошелек 1: {WALLET_1}")
    print(f"💰 Кошелек 2: {WALLET_2}")
    print()
    
    print("🔍 НАЧИНАЕМ ТЕСТ...")
    print()
    
    test_duration = 200  # 200 секунд
    interval = 20  # 20 секунд
    
    for cycle in range(test_duration // interval):
        print(f"🔄 ЦИКЛ {cycle + 1}/10 - {datetime.now().strftime('%H:%M:%S')}")
        
        # Симулируем смену кошелька
        expected_wallet = simulate_wallet_change()
        print(f"📤 Ожидаемый кошелек: {expected_wallet}")
        
        # Проверяем, что возвращает наш бот
        our_bot_wallet = test_our_bot()
        print(f"🎯 Наш бот возвращает: {our_bot_wallet}")
        
        # Проверяем соответствие
        if our_bot_wallet == expected_wallet:
            print("  ✅ Наш бот показывает правильный кошелек")
        else:
            print("  ❌ Наш бот показывает неправильный кошелек")
            print(f"  📊 Ожидалось: {expected_wallet}")
            print(f"  📊 Получено: {our_bot_wallet}")
        
        print()
        
        # Ждем до следующего цикла
        if cycle < (test_duration // interval) - 1:
            print(f"⏳ Ждем {interval} секунд до следующего цикла...")
            time.sleep(interval)
    
    print("🏁 ТЕСТ ЗАВЕРШЕН!")
    print(f"📅 Время окончания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()





