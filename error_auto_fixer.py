#!/usr/bin/env python3
"""
🤖 АВТОМАТИЧЕСКИЙ ИСПРАВИТЕЛЬ ОШИБОК БОТА
==========================================
Отслеживает ошибки в логах бота и автоматически исправляет их
"""

import os
import sys
import time
import re
import subprocess
import signal
from datetime import datetime
from pathlib import Path

class ErrorAutoFixer:
    def __init__(self):
        self.bot_file = "bot_fondklik_correct.py"
        self.log_patterns = {
            # Ошибка редактирования сообщения с фото
            "There is no text in the message to edit": {
                "fix": "fix_photo_message_edit",
                "description": "Попытка редактировать сообщение с фото без текста"
            },
            # Конфликт ботов
            "Conflict: terminated by other getUpdates request": {
                "fix": "fix_bot_conflict", 
                "description": "Конфликт между несколькими ботами"
            },
            # Ошибки базы данных
            "no such table": {
                "fix": "fix_database_error",
                "description": "Отсутствует таблица в базе данных"
            },
            # Ошибки импорта
            "ModuleNotFoundError": {
                "fix": "fix_import_error",
                "description": "Отсутствует модуль"
            }
        }
        self.fixes_applied = []
        
    def monitor_logs(self):
        """Мониторинг логов в реальном времени"""
        print("🔍 Запуск мониторинга ошибок...")
        
        # Получаем PID бота
        bot_pid = self.get_bot_pid()
        if not bot_pid:
            print("❌ Бот не запущен")
            return
            
        print(f"📊 Мониторинг бота PID: {bot_pid}")
        
        # Отслеживаем вывод процесса
        try:
            process = subprocess.Popen(
                ["tail", "-f", f"/proc/{bot_pid}/fd/1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except:
            # Альтернативный способ для macOS
            try:
                process = subprocess.Popen(
                    ["ps", "-p", str(bot_pid), "-o", "command="],
                    stdout=subprocess.PIPE,
                    text=True
                )
            except:
                print("❌ Не удалось подключиться к процессу бота")
                return
        
        print("✅ Мониторинг запущен. Ожидание ошибок...")
        
        while True:
            try:
                line = process.stdout.readline()
                if line:
                    self.check_for_errors(line.strip())
                time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n🛑 Остановка мониторинга...")
                process.terminate()
                break
            except Exception as e:
                print(f"❌ Ошибка мониторинга: {e}")
                time.sleep(1)
    
    def check_for_errors(self, log_line):
        """Проверка строки лога на наличие ошибок"""
        for error_pattern, error_info in self.log_patterns.items():
            if error_pattern in log_line:
                print(f"\n🚨 ОБНАРУЖЕНА ОШИБКА: {error_info['description']}")
                print(f"📝 Строка: {log_line}")
                
                # Применяем исправление
                fix_method = getattr(self, error_info['fix'])
                if fix_method():
                    print(f"✅ Ошибка исправлена: {error_info['description']}")
                    self.fixes_applied.append({
                        "time": datetime.now(),
                        "error": error_pattern,
                        "description": error_info['description']
                    })
                else:
                    print(f"❌ Не удалось исправить: {error_info['description']}")
    
    def fix_photo_message_edit(self):
        """Исправление ошибки редактирования сообщения с фото"""
        print("🔧 Исправление ошибки редактирования фото...")
        
        # Читаем файл бота
        try:
            with open(self.bot_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return False
        
        # Ищем проблемные места с edit_message_text
        fixes = [
            # Заменяем edit_message_text на edit_message_media для сообщений с фото
            {
                "pattern": r'await update\.callback_query\.edit_message_text\(\s*text=([^,]+),\s*reply_markup=([^)]+)\)',
                "replacement": r'await update.callback_query.edit_message_media(\n            media=InputMediaPhoto(media="AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE", caption=\1),\n            reply_markup=\2\n        )'
            }
        ]
        
        original_content = content
        for fix in fixes:
            content = re.sub(fix["pattern"], fix["replacement"], content, flags=re.MULTILINE | re.DOTALL)
        
        # Если были изменения, сохраняем файл
        if content != original_content:
            try:
                # Создаем бэкап
                backup_name = f"{self.bot_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                with open(backup_name, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                print(f"💾 Создан бэкап: {backup_name}")
                
                # Сохраняем исправленную версию
                with open(self.bot_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Перезапускаем бота
                self.restart_bot()
                return True
            except Exception as e:
                print(f"❌ Ошибка сохранения: {e}")
                return False
        
        return False
    
    def fix_bot_conflict(self):
        """Исправление конфликта ботов"""
        print("🔧 Исправление конфликта ботов...")
        
        # Останавливаем все боты
        try:
            subprocess.run(["python3", "bot_auto_manager.py", "stop"], check=True)
            time.sleep(2)
            
            # Запускаем только нужный бот
            subprocess.run(["python3", "bot_auto_manager.py", "manage"], check=True)
            return True
        except Exception as e:
            print(f"❌ Ошибка исправления конфликта: {e}")
            return False
    
    def fix_database_error(self):
        """Исправление ошибок базы данных"""
        print("🔧 Исправление ошибки базы данных...")
        
        # Пересоздаем базу данных
        try:
            if os.path.exists("bot_database.db"):
                backup_name = f"bot_database.db.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename("bot_database.db", backup_name)
                print(f"💾 Создан бэкап БД: {backup_name}")
            
            # Перезапускаем бота для пересоздания БД
            self.restart_bot()
            return True
        except Exception as e:
            print(f"❌ Ошибка исправления БД: {e}")
            return False
    
    def fix_import_error(self):
        """Исправление ошибок импорта"""
        print("🔧 Исправление ошибки импорта...")
        
        try:
            # Устанавливаем недостающие модули
            subprocess.run(["pip3", "install", "-r", "requirements.txt"], check=True)
            return True
        except Exception as e:
            print(f"❌ Ошибка установки модулей: {e}")
            return False
    
    def restart_bot(self):
        """Перезапуск бота"""
        print("🔄 Перезапуск бота...")
        
        try:
            # Останавливаем бота
            subprocess.run(["python3", "bot_auto_manager.py", "stop"], check=True)
            time.sleep(2)
            
            # Запускаем бота
            subprocess.run(["python3", "bot_auto_manager.py", "manage"], check=True)
            print("✅ Бот перезапущен")
        except Exception as e:
            print(f"❌ Ошибка перезапуска: {e}")
    
    def get_bot_pid(self):
        """Получение PID бота"""
        try:
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True
            )
            
            for line in result.stdout.split('\n'):
                if self.bot_file in line and 'python3' in line:
                    parts = line.split()
                    if len(parts) > 1:
                        return int(parts[1])
            return None
        except Exception:
            return None
    
    def show_statistics(self):
        """Показать статистику исправлений"""
        print("\n📊 СТАТИСТИКА АВТОИСПРАВЛЕНИЙ")
        print("=" * 50)
        
        if not self.fixes_applied:
            print("✅ Ошибок не обнаружено")
            return
        
        for fix in self.fixes_applied:
            print(f"🕐 {fix['time'].strftime('%H:%M:%S')} - {fix['description']}")
        
        print(f"\n📈 Всего исправлено: {len(self.fixes_applied)}")

def main():
    """Главная функция"""
    print("🤖 АВТОМАТИЧЕСКИЙ ИСПРАВИТЕЛЬ ОШИБОК БОТА")
    print("=" * 50)
    
    fixer = ErrorAutoFixer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "monitor":
            fixer.monitor_logs()
        elif command == "stats":
            fixer.show_statistics()
        elif command == "test":
            # Тестируем исправление ошибки редактирования фото
            print("🧪 Тестирование исправления ошибки редактирования фото...")
            fixer.fix_photo_message_edit()
        else:
            print("❌ Неизвестная команда")
            print("Доступные команды: monitor, stats, test")
    else:
        print("Использование:")
        print("  python3 error_auto_fixer.py monitor  # Запуск мониторинга")
        print("  python3 error_auto_fixer.py stats    # Показать статистику")
        print("  python3 error_auto_fixer.py test     # Тестировать исправления")

if __name__ == "__main__":
    main()








