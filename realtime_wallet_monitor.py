#!/usr/bin/env python3
"""
Мониторинг активного кошелька в реальном времени
"""

import time
from datetime import datetime
from payment_client import payment_client

def get_current_wallet():
    """Получаем текущий кошелек"""
    try:
        result = payment_client.get_payment_wallet("TJR44gwdyGhLa4833zJtutNepRoNVFpMzX")
        if result.get("success"):
            return result.get("wallet_address", "Неизвестно")
        else:
            return f"Ошибка: {result.get('error', 'Неизвестная ошибка')}"
    except Exception as e:
        return f"Ошибка: {e}"

def main():
    print("🔍 МОНИТОРИНГ АКТИВНОГО КОШЕЛЬКА В РЕАЛЬНОМ ВРЕМЕНИ")
    print("=" * 60)
    print(f"📅 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Интервал проверки: 5 секунд")
    print()
    
    previous_wallet = None
    check_count = 0
    
    try:
        while True:
            check_count += 1
            current_wallet = get_current_wallet()
            current_time = datetime.now().strftime('%H:%M:%S')
            
            print(f"[{current_time}] Проверка #{check_count}: {current_wallet}")
            
            # Проверяем, изменился ли кошелек
            if previous_wallet is not None and previous_wallet != current_wallet:
                print(f"🔄 ИЗМЕНЕНИЕ КОШЕЛЬКА ОБНАРУЖЕНО!")
                print(f"   Было: {previous_wallet}")
                print(f"   Стало: {current_wallet}")
                print(f"   Время: {current_time}")
                print()
            
            previous_wallet = current_wallet
            
            # Ждем 5 секунд до следующей проверки
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Мониторинг остановлен пользователем")

if __name__ == "__main__":
    main()





