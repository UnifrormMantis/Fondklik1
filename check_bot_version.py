#!/usr/bin/env python3
"""
Скрипт для проверки актуальности запущенного бота
Автоматически проверяет и переключает на версию с наивысшим приоритетом
"""

import os
import sys
import subprocess
import psutil
from datetime import datetime

# Приоритеты версий ботов (от высшего к низшему)
BOT_PRIORITIES = {
    "bot_fondklik_correct.py": 1,      # Высший приоритет
    "bot_final_backup.py": 2,
    "bot_final_backup_simple.py": 3,
    "bot_final_backup_clean.py": 4,
    "bot_final_backup_working.py": 5,
    "bot_full_working.py": 6,
    "bot_full_version.py": 7,
    "bot_final.py": 8,
    "bot_final_clean.py": 9,
    "bot_fondklik.py": 10,
    "bot.py": 11                       # Низший приоритет
}

def get_running_bots():
    """Получить список запущенных ботов"""
    running_bots = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == 'Python' and proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                for bot_name in BOT_PRIORITIES.keys():
                    if bot_name in cmdline:
                        running_bots.append({
                            'pid': proc.info['pid'],
                            'name': bot_name,
                            'priority': BOT_PRIORITIES[bot_name],
                            'cmdline': cmdline
                        })
                        break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return running_bots

def get_highest_priority_bot():
    """Получить бота с наивысшим приоритетом"""
    return min(BOT_PRIORITIES.items(), key=lambda x: x[1])

def check_bot_features(bot_name):
    """Проверить наличие ключевых функций в боте"""
    if not os.path.exists(bot_name):
        return False
    
    try:
        with open(bot_name, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Проверяем наличие ключевых функций
        features = {
            'delete_wallet': '🗑️ Удалить кошелек' in content,
            'change_wallet': '✏️ Изменить кошелек' in content,
            'handle_photo': 'async def handle_photo' in content,
            'remove_wallet_address': 'def remove_wallet_address' in content
        }
        
        return features
    except Exception as e:
        print(f"   ❌ Ошибка чтения файла {bot_name}: {e}")
        return False

def check_bot_versions():
    """Проверить актуальность запущенных ботов"""
    print(f"🔍 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Проверка версий ботов")
    print("=" * 60)
    
    running_bots = get_running_bots()
    
    if not running_bots:
        print("❌ Боты не запущены")
        return False
    
    print(f"📊 Найдено запущенных ботов: {len(running_bots)}")
    
    # Показываем запущенные боты с проверкой функций
    for bot in running_bots:
        features = check_bot_features(bot['name'])
        if features:
            feature_status = "✅" if all(features.values()) else "⚠️"
            print(f"   - PID {bot['pid']}: {bot['name']} (приоритет: {bot['priority']}) {feature_status}")
            if not all(features.values()):
                missing = [k for k, v in features.items() if not v]
                print(f"     ❌ Отсутствуют функции: {', '.join(missing)}")
        else:
            print(f"   - PID {bot['pid']}: {bot['name']} (приоритет: {bot['priority']}) ❌")
    
    # Находим бота с наивысшим приоритетом
    highest_priority_bot = min(running_bots, key=lambda x: x['priority'])
    highest_priority_name, highest_priority_value = get_highest_priority_bot()
    
    print(f"\n🎯 Бот с наивысшим приоритетом: {highest_priority_bot['name']} (приоритет: {highest_priority_bot['priority']})")
    
    # Проверяем функции у бота с наивысшим приоритетом
    features = check_bot_features(highest_priority_name)
    if features and all(features.values()):
        print("✅ Запущена актуальная версия бота со всеми функциями!")
        return True
    else:
        print(f"⚠️  Запущена устаревшая версия! Актуальная: {highest_priority_name}")
        if features:
            missing = [k for k, v in features.items() if not v]
            print(f"   ❌ Отсутствуют функции: {', '.join(missing)}")
        return False

def auto_fix_bot_versions():
    """Автоматически исправить версии ботов"""
    print(f"🔧 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Автоматическое исправление версий")
    print("=" * 60)
    
    running_bots = get_running_bots()
    
    if not running_bots:
        print("❌ Боты не запущены")
        return False
    
    # Находим бота с наивысшим приоритетом среди запущенных
    highest_priority_bot = min(running_bots, key=lambda x: x['priority'])
    highest_priority_name, highest_priority_value = get_highest_priority_bot()
    
    # Если запущен не самый приоритетный бот
    if highest_priority_bot['priority'] != highest_priority_value:
        print(f"🔄 Переключаемся с {highest_priority_bot['name']} на {highest_priority_name}")
        
        # Останавливаем все боты
        for bot in running_bots:
            try:
                print(f"   🛑 Останавливаю PID {bot['pid']}: {bot['name']}")
                os.kill(bot['pid'], 9)  # SIGKILL
            except ProcessLookupError:
                print(f"   ⚠️  Процесс {bot['pid']} уже завершен")
            except PermissionError:
                print(f"   ❌ Нет прав для остановки процесса {bot['pid']}")
        
        # Запускаем актуальную версию
        if os.path.exists(highest_priority_name):
            print(f"   🚀 Запускаю {highest_priority_name}")
            try:
                subprocess.Popen([sys.executable, highest_priority_name], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
                print(f"   ✅ {highest_priority_name} успешно запущен")
                return True
            except Exception as e:
                print(f"   ❌ Ошибка запуска {highest_priority_name}: {e}")
                return False
        else:
            print(f"   ❌ Файл {highest_priority_name} не найден")
            return False
    else:
        print("✅ Уже запущена актуальная версия")
        return True

def main():
    """Главная функция"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "check":
            check_bot_versions()
        elif command == "fix":
            auto_fix_bot_versions()
        elif command == "status":
            running_bots = get_running_bots()
            if running_bots:
                print("📊 Запущенные боты:")
                for bot in running_bots:
                    print(f"   - PID {bot['pid']}: {bot['name']} (приоритет: {bot['priority']})")
            else:
                print("❌ Боты не запущены")
        else:
            print("Использование:")
            print("  python3 check_bot_version.py check  - Проверить версии")
            print("  python3 check_bot_version.py fix    - Автоматически исправить")
            print("  python3 check_bot_version.py status - Показать статус")
    else:
        # По умолчанию - проверка
        check_bot_versions()

if __name__ == "__main__":
    main()
