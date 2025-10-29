#!/usr/bin/env python3
"""
Скрипт для проверки и остановки всех экземпляров ботов
"""

import subprocess
import sys
import time

def check_running_bots():
    """Проверить запущенные боты"""
    try:
        # Ищем все процессы с ботом
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        bot_processes = []
        for line in lines:
            if 'python3' in line and 'bot' in line and 'grep' not in line:
                bot_processes.append(line)
        
        return bot_processes
    except Exception as e:
        print(f"Ошибка при проверке процессов: {e}")
        return []

def stop_all_bots():
    """Остановить все боты"""
    print("🔍 Поиск запущенных ботов...")
    
    # Останавливаем все процессы с ботом
    commands = [
        "pkill -f 'python3 bot'",
        "pkill -f 'bot_final'",
        "pkill -f 'bot_final_backup'",
        "pkill -f 'bot.py'"
    ]
    
    for cmd in commands:
        try:
            subprocess.run(cmd, shell=True, capture_output=True)
            print(f"✅ Выполнено: {cmd}")
        except Exception as e:
            print(f"❌ Ошибка при выполнении {cmd}: {e}")
    
    # Ждем немного
    time.sleep(2)
    
    # Проверяем, что все остановлено
    remaining = check_running_bots()
    if remaining:
        print(f"⚠️  Остались запущенные процессы:")
        for proc in remaining:
            print(f"   {proc}")
        
        # Принудительно убиваем
        print("🔨 Принудительная остановка...")
        subprocess.run("pkill -9 -f 'python3 bot'", shell=True)
        time.sleep(1)
    else:
        print("✅ Все боты остановлены!")

def main():
    print("🤖 УПРАВЛЕНИЕ БОТАМИ")
    print("=" * 40)
    
    # Показываем текущие процессы
    print("\n📊 Текущие процессы с ботом:")
    processes = check_running_bots()
    if processes:
        for i, proc in enumerate(processes, 1):
            print(f"{i}. {proc}")
    else:
        print("   Нет запущенных ботов")
    
    # Останавливаем все
    print("\n🛑 Остановка всех ботов...")
    stop_all_bots()
    
    # Финальная проверка
    print("\n🔍 Финальная проверка:")
    final_check = check_running_bots()
    if final_check:
        print("❌ Остались процессы:")
        for proc in final_check:
            print(f"   {proc}")
    else:
        print("✅ Все боты успешно остановлены!")
        print("\n💡 Теперь можно запустить один бот:")
        print("   python3 bot_final_backup_simple.py")

if __name__ == "__main__":
    main()








