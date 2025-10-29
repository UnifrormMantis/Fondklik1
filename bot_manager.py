#!/usr/bin/env python3
"""
Менеджер ботов - система контроля для предотвращения множественного запуска
Отслеживает точное количество активных ботов и не допускает больше одной версии
"""

import os
import sys
import time
import signal
import subprocess
import json
from datetime import datetime

class BotManager:
    def __init__(self):
        self.lock_file = "bot_manager.lock"
        self.pid_file = "bot.pid"
        self.max_bots = 1
        self.bot_process_name = "bot_final.py"
        
    def get_running_bots(self):
        """Получить список всех запущенных ботов"""
        running_bots = []
        try:
            # Используем ps для поиска процессов
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if self.bot_process_name in line and 'grep' not in line:
                    parts = line.split()
                    if len(parts) > 1:
                        try:
                            pid = int(parts[1])
                            running_bots.append({
                                'pid': pid,
                                'name': parts[0],
                                'cmdline': line
                            })
                        except (ValueError, IndexError):
                            continue
        except Exception as e:
            print(f"⚠️  Ошибка поиска процессов: {e}")
        
        return running_bots
    
    def is_bot_running(self):
        """Проверить, запущен ли бот"""
        return len(self.get_running_bots()) > 0
    
    def get_bot_count(self):
        """Получить точное количество запущенных ботов"""
        return len(self.get_running_bots())
    
    def stop_all_bots(self):
        """Остановить все боты"""
        running_bots = self.get_running_bots()
        if not running_bots:
            print("ℹ️  Боты не запущены")
            return True
        
        print(f"🛑 Найдено {len(running_bots)} ботов. Останавливаю...")
        
        for bot in running_bots:
            try:
                os.kill(bot['pid'], signal.SIGTERM)
                print(f"🔄 Остановка бота PID {bot['pid']}...")
            except (ProcessLookupError, PermissionError):
                print(f"⚠️  Не удалось остановить PID {bot['pid']}")
        
        # Ждем завершения
        time.sleep(3)
        
        # Принудительная остановка если не завершились
        remaining_bots = self.get_running_bots()
        if remaining_bots:
            print("🔄 Принудительная остановка...")
        for bot in remaining_bots:
            try:
                os.kill(bot['pid'], signal.SIGKILL)
                print(f"💀 Принудительная остановка PID {bot['pid']}")
            except (ProcessLookupError, PermissionError):
                pass
        
        # Очищаем файлы
        self.cleanup_files()
        
        final_count = self.get_bot_count()
        if final_count == 0:
            print("✅ Все боты остановлены")
            return True
        else:
            print(f"❌ Осталось {final_count} ботов")
            return False
    
    def cleanup_files(self):
        """Очистить файлы блокировки"""
        files_to_remove = [self.lock_file, self.pid_file, "bot.lock"]
        for file in files_to_remove:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    print(f"🗑️  Удален файл {file}")
                except OSError:
                    pass
    
    def start_bot(self):
        """Запустить бота с проверкой"""
        # Проверяем количество ботов
        current_count = self.get_bot_count()
        
        if current_count >= self.max_bots:
            print(f"❌ Превышено максимальное количество ботов ({self.max_bots})")
            print(f"📊 Текущее количество: {current_count}")
            print("🛑 Сначала остановите существующие боты")
            return False
        
        if current_count > 0:
            print(f"⚠️  Уже запущено {current_count} ботов")
            print("🛑 Остановите их перед запуском нового")
            return False
        
        print("🚀 Запуск бота...")
        
        try:
            # Запускаем бота в фоне
            process = subprocess.Popen(
                [sys.executable, self.bot_process_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Сохраняем PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Ждем немного и проверяем
            time.sleep(3)
            
            if self.is_bot_running():
                print(f"✅ Бот успешно запущен (PID: {process.pid})")
                print(f"📊 Активных ботов: {self.get_bot_count()}")
                return True
            else:
                print("❌ Бот не запустился")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
            return False
    
    def status(self):
        """Показать статус ботов"""
        running_bots = self.get_running_bots()
        count = len(running_bots)
        
        print(f"📊 Статус ботов:")
        print(f"   Активных: {count}/{self.max_bots}")
        
        if count > 0:
            print("   Запущенные боты:")
            for bot in running_bots:
                print(f"   - PID {bot['pid']}: {bot['cmdline']}")
        else:
            print("   Боты не запущены")
    
    def monitor(self):
        """Мониторинг ботов (запуск в фоне)"""
        print("🔍 Запуск мониторинга ботов...")
        
        while True:
            count = self.get_bot_count()
            
            if count > self.max_bots:
                print(f"⚠️  Обнаружено {count} ботов (максимум {self.max_bots})")
                print("🛑 Останавливаю лишние...")
                self.stop_all_bots()
            
            time.sleep(5)

def main():
    manager = BotManager()
    
    if len(sys.argv) < 2:
        print("🤖 Менеджер ботов")
        print("Использование:")
        print("  python3 bot_manager.py start    - Запустить бота")
        print("  python3 bot_manager.py stop     - Остановить всех ботов")
        print("  python3 bot_manager.py status   - Показать статус")
        print("  python3 bot_manager.py monitor  - Мониторинг (фоновый режим)")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        if manager.start_bot():
            print("🎉 Бот запущен успешно!")
        else:
            print("❌ Не удалось запустить бота")
            sys.exit(1)
    
    elif command == "stop":
        if manager.stop_all_bots():
            print("🎉 Все боты остановлены!")
        else:
            print("❌ Не удалось остановить всех ботов")
            sys.exit(1)
    
    elif command == "status":
        manager.status()
    
    elif command == "monitor":
        try:
            manager.monitor()
        except KeyboardInterrupt:
            print("\n🛑 Мониторинг остановлен")
    
    else:
        print(f"❌ Неизвестная команда: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
