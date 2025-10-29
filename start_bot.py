#!/usr/bin/env python3
"""
Скрипт для запуска бота с правильными настройками
"""

import os
import sys
import subprocess
import time

def kill_existing_bots():
    """Остановить все существующие процессы бота"""
    try:
        # Останавливаем все процессы python3
        subprocess.run(['pkill', '-f', 'python3'], check=False)
        print("🛑 Остановлены все процессы Python")
        time.sleep(3)
    except Exception as e:
        print(f"⚠️ Ошибка при остановке процессов: {e}")

def start_bot():
    """Запустить бота"""
    try:
        print("🚀 Запуск бота...")
        # Запускаем бота в фоновом режиме
        process = subprocess.Popen(['python3', 'bot.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        print(f"✅ Бот запущен с PID: {process.pid}")
        print("📱 Теперь можете тестировать бота в Telegram")
        print("🛑 Для остановки нажмите Ctrl+C")
        
        # Ждем завершения
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
        process.terminate()
        print("✅ Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    print("🤖 Запуск Telegram Crypto Bot")
    print("=" * 40)
    
    # Останавливаем существующие процессы
    kill_existing_bots()
    
    # Запускаем бота
    start_bot()

















