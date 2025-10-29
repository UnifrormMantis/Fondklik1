#!/usr/bin/env python3
"""
Скрипт для смены кошелька каждые 20 секунд
"""

import time
from datetime import datetime

# Два кошелька для тестирования
WALLET_1 = "TWJ5wQPnJTk2keYXjEgf19i17ZzACBY4Mx"
WALLET_2 = "TRpxhgJ9izoZ56iHJ6gkWwvuStaMeCTisS"

def change_wallet_in_bot(wallet):
    """Меняем кошелек в боте"""
    try:
        # Читаем файл бота
        with open('bot_fondklik_correct.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем кошелек
        old_wallet = 'payment_wallet = "ВАШ_АКТУАЛЬНЫЙ_КОШЕЛЕК_ЗДЕСЬ"'
        new_wallet = f'payment_wallet = "{wallet}"'
        
        if old_wallet in content:
            content = content.replace(old_wallet, new_wallet)
        else:
            # Ищем другой паттерн
            import re
            pattern = r'payment_wallet = "[^"]*"'
            content = re.sub(pattern, f'payment_wallet = "{wallet}"', content)
        
        # Записываем обратно
        with open('bot_fondklik_correct.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Кошелек изменен на: {wallet}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка изменения кошелька: {e}")
        return False

def main():
    print("🚀 ЗАПУСК СМЕНЫ КОШЕЛЬКОВ КАЖДЫЕ 20 СЕКУНД")
    print("=" * 60)
    print(f"📅 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Интервал смены: 20 секунд")
    print(f"🔄 Общее время: 200 секунд")
    print(f"💰 Кошелек 1: {WALLET_1}")
    print(f"💰 Кошелек 2: {WALLET_2}")
    print()
    
    current_wallet = WALLET_1
    test_duration = 200  # 200 секунд
    interval = 20  # 20 секунд
    
    for cycle in range(test_duration // interval):
        print(f"🔄 ЦИКЛ {cycle + 1}/10 - {datetime.now().strftime('%H:%M:%S')}")
        print(f"📤 Меняем кошелек на: {current_wallet}")
        
        # Меняем кошелек в боте
        if change_wallet_in_bot(current_wallet):
            print(f"✅ Кошелек успешно изменен")
        else:
            print(f"❌ Ошибка изменения кошелька")
        
        print()
        
        # Меняем кошелек для следующего цикла
        current_wallet = WALLET_2 if current_wallet == WALLET_1 else WALLET_1
        
        # Ждем до следующего цикла
        if cycle < (test_duration // interval) - 1:
            print(f"⏳ Ждем {interval} секунд до следующего цикла...")
            time.sleep(interval)
    
    print("🏁 СМЕНА КОШЕЛЬКОВ ЗАВЕРШЕНА!")
    print(f"📅 Время окончания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()





