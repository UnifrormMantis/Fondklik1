#!/usr/bin/env python3
"""
Автоматический менеджер ботов - система контроля версий
Отслеживает все запущенные версии ботов и оставляет только последнюю
"""

import os
import sys
import time
import signal
import subprocess
import json
import psutil
import threading
import queue
from datetime import datetime
from pathlib import Path

class BotAutoManager:
    def __init__(self):
        self.lock_file = "bot_auto_manager.lock"
        self.status_file = "bot_status.json"
        self.log_queue = queue.Queue()
        self.monitoring_active = False
        self.bot_versions = [
            "bot_fondklik_correct.py",
            "bot_final_backup.py", 
            "bot_final_backup_simple.py",
            "bot_final_backup_clean.py",
            "bot_final_backup_working.py",
            "bot_full_working.py",
            "bot_full_version.py",
            "bot_final.py",
            "bot_final_clean.py",
            "bot_fondklik.py",
            "bot.py"
        ]
        self.priority_order = {
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

    def get_running_bots(self):
        """Получить список всех запущенных ботов с их версиями"""
        running_bots = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if proc.info['name'] == 'Python' and proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    
                    # Ищем запущенные боты
                    for version in self.bot_versions:
                        if version in cmdline:
                            running_bots.append({
                                'pid': proc.info['pid'],
                                'version': version,
                                'cmdline': cmdline,
                                'start_time': proc.info['create_time'],
                                'priority': self.priority_order.get(version, 999)
                            })
                            break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return running_bots

    def stop_all_bots(self):
        """Остановить все запущенные боты"""
        print("🛑 Остановка всех ботов...")
        
        # Сначала мягкая остановка
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'Python' and proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if any(version in cmdline for version in self.bot_versions):
                        print(f"   Останавливаю PID {proc.info['pid']}: {cmdline}")
                        proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Ждем 3 секунды
        time.sleep(3)
        
        # Принудительная остановка если нужно
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'Python' and proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if any(version in cmdline for version in self.bot_versions):
                        if proc.is_running():
                            print(f"   Принудительно останавливаю PID {proc.info['pid']}")
                            proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def get_highest_priority_bot(self, running_bots):
        """Получить бота с наивысшим приоритетом"""
        if not running_bots:
            return None
            
        # Сортируем по приоритету (меньше число = выше приоритет)
        sorted_bots = sorted(running_bots, key=lambda x: x['priority'])
        return sorted_bots[0]

    def start_bot(self, bot_version):
        """Запустить бота"""
        if not os.path.exists(bot_version):
            print(f"❌ Файл {bot_version} не найден")
            return False
            
        print(f"🚀 Запускаю {bot_version}...")
        
        try:
            # Запускаем в фоне
            process = subprocess.Popen(
                [sys.executable, bot_version],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Ждем немного и проверяем, что процесс запустился
            time.sleep(2)
            if process.poll() is None:
                print(f"✅ {bot_version} успешно запущен (PID: {process.pid})")
                self.save_status(bot_version, process.pid)
                return True
            else:
                print(f"❌ {bot_version} не запустился")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запуска {bot_version}: {e}")
            return False

    def save_status(self, bot_version, pid):
        """Сохранить статус бота"""
        status = {
            'active_bot': bot_version,
            'pid': pid,
            'start_time': datetime.now().isoformat(),
            'last_check': datetime.now().isoformat()
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)

    def load_status(self):
        """Загрузить статус бота"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None

    def cleanup_old_files(self):
        """Очистить старые файлы блокировок"""
        lock_files = [
            "bot.lock",
            "bot_manager.lock", 
            "bot_auto_manager.lock"
        ]
        
        for lock_file in lock_files:
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                    print(f"🗑️ Удален файл блокировки: {lock_file}")
                except:
                    pass

    def monitor_logs(self):
        """Мониторинг логов на предмет ошибок 409 Conflict"""
        print("🔍 Запуск мониторинга логов...")
        
        # Ищем все возможные лог-файлы
        log_files = []
        for version in self.bot_versions:
            log_file = version.replace('.py', '.log')
            if os.path.exists(log_file):
                log_files.append(log_file)
        
        # Добавляем общие лог-файлы
        common_logs = [
            "bot_auto_manager.log",
            "bot_manager.log",
            "nohup.out"
        ]
        
        for log_file in common_logs:
            if os.path.exists(log_file):
                log_files.append(log_file)
        
        if not log_files:
            print("📭 Лог-файлы не найдены, создаю мониторинг терминала...")
            self.monitor_terminal_output()
            return
        
        print(f"📄 Мониторинг лог-файлов: {', '.join(log_files)}")
        
        # Отслеживаем изменения в лог-файлах
        last_positions = {}
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    f.seek(0, 2)  # Переходим в конец файла
                    last_positions[log_file] = f.tell()
            except:
                last_positions[log_file] = 0
        
        while self.monitoring_active:
            try:
                for log_file in log_files:
                    if not os.path.exists(log_file):
                        continue
                        
                    try:
                        with open(log_file, 'r') as f:
                            f.seek(last_positions[log_file])
                            new_content = f.read()
                            
                            if new_content:
                                # Проверяем на ошибки 409 Conflict
                                if "409 Conflict" in new_content or "terminated by other getUpdates request" in new_content:
                                    print(f"\n🚨 ОБНАРУЖЕНА ОШИБКА 409 CONFLICT в {log_file}!")
                                    print("🔄 Запускаю автоматическую проверку...")
                                    self.log_queue.put("conflict_detected")
                                
                                last_positions[log_file] = f.tell()
                    except Exception as e:
                        print(f"❌ Ошибка чтения {log_file}: {e}")
                
                time.sleep(2)  # Проверяем каждые 2 секунды
                
            except Exception as e:
                print(f"❌ Ошибка мониторинга логов: {e}")
                time.sleep(5)

    def monitor_terminal_output(self):
        """Мониторинг вывода терминала на предмет ошибок"""
        print("🖥️ Мониторинг вывода терминала...")
        
        # Запускаем команду для мониторинга процессов Python
        try:
            process = subprocess.Popen(
                ['ps', 'aux'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            while self.monitoring_active:
                try:
                    # Проверяем запущенные процессы ботов
                    running_bots = self.get_running_bots()
                    
                    if len(running_bots) > 1:
                        print(f"\n⚠️ Обнаружено {len(running_bots)} ботов в процессах!")
                        self.log_queue.put("multiple_bots_detected")
                    
                    time.sleep(5)  # Проверяем каждые 5 секунд
                    
                except Exception as e:
                    print(f"❌ Ошибка мониторинга процессов: {e}")
                    time.sleep(10)
                    
        except Exception as e:
            print(f"❌ Ошибка запуска мониторинга терминала: {e}")

    def start_log_monitoring(self):
        """Запустить мониторинг логов в отдельном потоке"""
        self.monitoring_active = True
        log_thread = threading.Thread(target=self.monitor_logs, daemon=True)
        log_thread.start()
        return log_thread

    def manage_bots(self):
        """Основная функция управления ботами"""
        print("🤖 АВТОМАТИЧЕСКИЙ МЕНЕДЖЕР БОТОВ")
        print("=" * 50)
        
        # Очищаем старые файлы блокировок
        self.cleanup_old_files()
        
        # Получаем список запущенных ботов
        running_bots = self.get_running_bots()
        
        print(f"📊 Найдено запущенных ботов: {len(running_bots)}")
        
        if running_bots:
            print("\n🔍 Запущенные боты:")
            for bot in running_bots:
                print(f"   - PID {bot['pid']}: {bot['version']} (приоритет: {bot['priority']})")
            
            # Получаем бота с наивысшим приоритетом
            highest_priority_bot = self.get_highest_priority_bot(running_bots)
            
            if highest_priority_bot:
                print(f"\n🎯 Бот с наивысшим приоритетом: {highest_priority_bot['version']}")
                
                # Останавливаем всех остальных
                bots_to_stop = [bot for bot in running_bots if bot['pid'] != highest_priority_bot['pid']]
                
                if bots_to_stop:
                    print(f"\n🛑 Останавливаю {len(bots_to_stop)} ботов с низким приоритетом...")
                    for bot in bots_to_stop:
                        try:
                            proc = psutil.Process(bot['pid'])
                            print(f"   Останавливаю PID {bot['pid']}: {bot['version']}")
                            proc.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    # Ждем завершения
                    time.sleep(3)
                    
                    # Принудительно завершаем если нужно
                    for bot in bots_to_stop:
                        try:
                            proc = psutil.Process(bot['pid'])
                            if proc.is_running():
                                print(f"   Принудительно завершаю PID {bot['pid']}")
                                proc.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                
                print(f"\n✅ Оставлен только {highest_priority_bot['version']} (PID: {highest_priority_bot['pid']})")
                self.save_status(highest_priority_bot['version'], highest_priority_bot['pid'])
                
            else:
                print("❌ Не удалось определить бота с наивысшим приоритетом")
                self.stop_all_bots()
        else:
            print("\n📭 Запущенных ботов не найдено")
            
            # Пытаемся запустить бота с наивысшим приоритетом
            for version in sorted(self.priority_order.keys(), key=lambda x: self.priority_order[x]):
                if os.path.exists(version):
                    print(f"\n🚀 Запускаю {version}...")
                    if self.start_bot(version):
                        break
                    else:
                        print(f"❌ Не удалось запустить {version}, пробую следующую версию...")

    def monitor_loop(self):
        """Цикл мониторинга"""
        print("🔄 Запуск мониторинга...")
        
        # Запускаем мониторинг логов в отдельном потоке
        log_thread = self.start_log_monitoring()
        
        while True:
            try:
                # Проверяем события из очереди логов
                try:
                    event = self.log_queue.get_nowait()
                    if event == "conflict_detected":
                        print("\n🚨 ОБРАБОТКА СОБЫТИЯ: Обнаружена ошибка 409 Conflict!")
                        self.manage_bots()
                    elif event == "multiple_bots_detected":
                        print("\n🚨 ОБРАБОТКА СОБЫТИЯ: Обнаружено несколько ботов!")
                        self.manage_bots()
                except queue.Empty:
                    pass
                
                # Обычная проверка состояния ботов
                running_bots = self.get_running_bots()
                
                if len(running_bots) > 1:
                    print(f"\n⚠️ Обнаружено {len(running_bots)} ботов! Управляю...")
                    self.manage_bots()
                elif len(running_bots) == 1:
                    bot = running_bots[0]
                    # Проверяем, что процесс еще жив
                    try:
                        proc = psutil.Process(bot['pid'])
                        if not proc.is_running():
                            print(f"\n💀 Бот {bot['version']} (PID: {bot['pid']}) завершился")
                            self.manage_bots()
                    except psutil.NoSuchProcess:
                        print(f"\n💀 Бот {bot['version']} (PID: {bot['pid']}) завершился")
                        self.manage_bots()
                else:
                    print(f"\n📭 Боты не запущены, запускаю...")
                    self.manage_bots()
                
                # Ждем 30 секунд перед следующей проверкой
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n🛑 Остановка мониторинга...")
                self.monitoring_active = False
                break
            except Exception as e:
                print(f"\n❌ Ошибка мониторинга: {e}")
                time.sleep(10)

def main():
    if len(sys.argv) < 2:
        print("🤖 АВТОМАТИЧЕСКИЙ МЕНЕДЖЕР БОТОВ")
        print("Использование:")
        print("  python3 bot_auto_manager.py manage    - Управление ботами (однократно)")
        print("  python3 bot_auto_manager.py monitor   - Мониторинг (постоянно)")
        print("  python3 bot_auto_manager.py stop      - Остановить всех ботов")
        print("  python3 bot_auto_manager.py status    - Показать статус")
        print("  python3 bot_auto_manager.py test      - Тест обнаружения ошибок")
        return

    manager = BotAutoManager()
    command = sys.argv[1].lower()

    if command == "manage":
        manager.manage_bots()
    elif command == "monitor":
        manager.monitor_loop()
    elif command == "stop":
        manager.stop_all_bots()
        print("✅ Все боты остановлены")
    elif command == "status":
        running_bots = manager.get_running_bots()
        print(f"📊 Запущено ботов: {len(running_bots)}")
        for bot in running_bots:
            print(f"   - PID {bot['pid']}: {bot['version']} (приоритет: {bot['priority']})")
    elif command == "test":
        print("🧪 ТЕСТ ОБНАРУЖЕНИЯ ОШИБОК 409 CONFLICT")
        print("=" * 50)
        
        # Создаем тестовый лог-файл с ошибкой
        test_log = "test_conflict.log"
        with open(test_log, 'w') as f:
            f.write("2025-10-07 13:35:16,342 - telegram.ext.Application - ERROR - No error handlers are registered, logging exception.\n")
            f.write("telegram.error.Conflict: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running\n")
        
        print(f"📄 Создан тестовый лог-файл: {test_log}")
        print("🔍 Запускаю мониторинг на 10 секунд...")
        
        # Запускаем мониторинг
        manager.monitoring_active = True
        log_thread = manager.start_log_monitoring()
        
        # Ждем 10 секунд
        time.sleep(10)
        
        # Останавливаем мониторинг
        manager.monitoring_active = False
        
        # Удаляем тестовый файл
        if os.path.exists(test_log):
            os.remove(test_log)
            print(f"🗑️ Удален тестовый файл: {test_log}")
        
        print("✅ Тест завершен")
    else:
        print("❌ Неизвестная команда")

if __name__ == "__main__":
    main()
