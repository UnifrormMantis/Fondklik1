#!/usr/bin/env python3
"""
Демон для постоянной работы Telegram бота
Автоматически перезапускает бота при сбоях
"""

import os
import sys
import time
import signal
import subprocess
import threading
from datetime import datetime

class BotDaemon:
    def __init__(self):
        self.bot_process = None
        self.running = False
        self.restart_count = 0
        self.max_restarts = 10
        self.restart_delay = 5
        self.bot_script = "bot_final.py"
        self.log_file = "daemon.log"
        
    def log(self, message):
        """Записать сообщение в лог"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    
    def start_bot(self):
        """Запустить бота"""
        try:
            self.log("🚀 Запуск бота...")
            
            # Останавливаем все существующие боты
            subprocess.run(["python3", "bot_manager.py", "stop"], 
                         capture_output=True, timeout=10)
            
            # Запускаем бота
            self.bot_process = subprocess.Popen(
                [sys.executable, self.bot_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.log(f"✅ Бот запущен (PID: {self.bot_process.pid})")
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка запуска бота: {e}")
            return False
    
    def stop_bot(self):
        """Остановить бота"""
        if self.bot_process and self.bot_process.poll() is None:
            self.log("🛑 Остановка бота...")
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=10)
                self.log("✅ Бот остановлен")
            except subprocess.TimeoutExpired:
                self.log("🔄 Принудительная остановка...")
                self.bot_process.kill()
                self.bot_process.wait()
                self.log("💀 Бот принудительно остановлен")
            except Exception as e:
                self.log(f"❌ Ошибка остановки: {e}")
    
    def is_bot_running(self):
        """Проверить, работает ли бот"""
        return self.bot_process and self.bot_process.poll() is None
    
    def monitor_bot(self):
        """Мониторинг бота"""
        while self.running:
            if not self.is_bot_running():
                if self.running:  # Проверяем, что демон еще работает
                    self.log("⚠️  Бот остановился")
                    
                    if self.restart_count < self.max_restarts:
                        self.restart_count += 1
                        self.log(f"🔄 Перезапуск #{self.restart_count} через {self.restart_delay} сек...")
                        
                        time.sleep(self.restart_delay)
                        
                        if self.running:  # Проверяем еще раз
                            if self.start_bot():
                                self.log("✅ Бот перезапущен успешно")
                            else:
                                self.log("❌ Не удалось перезапустить бота")
                    else:
                        self.log(f"❌ Превышено максимальное количество перезапусков ({self.max_restarts})")
                        self.running = False
            else:
                # Сбрасываем счетчик перезапусков при успешной работе
                if self.restart_count > 0:
                    self.log("✅ Бот работает стабильно, сброс счетчика перезапусков")
                    self.restart_count = 0
            
            time.sleep(5)  # Проверяем каждые 5 секунд
    
    def start_daemon(self):
        """Запустить демон"""
        self.log("🤖 Запуск демона бота...")
        self.running = True
        
        # Запускаем бота
        if not self.start_bot():
            self.log("❌ Не удалось запустить бота")
            return False
        
        # Запускаем мониторинг в отдельном потоке
        monitor_thread = threading.Thread(target=self.monitor_bot, daemon=True)
        monitor_thread.start()
        
        self.log("✅ Демон запущен")
        return True
    
    def stop_daemon(self):
        """Остановить демон"""
        self.log("🛑 Остановка демона...")
        self.running = False
        
        self.stop_bot()
        
        self.log("✅ Демон остановлен")
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов"""
        self.log(f"📡 Получен сигнал {signum}")
        self.stop_daemon()
        sys.exit(0)

def main():
    daemon = BotDaemon()
    
    # Устанавливаем обработчики сигналов
    signal.signal(signal.SIGINT, daemon.signal_handler)
    signal.signal(signal.SIGTERM, daemon.signal_handler)
    
    if len(sys.argv) < 2:
        print("🤖 Демон Telegram бота")
        print("Использование:")
        print("  python3 bot_daemon.py start   - Запустить демон")
        print("  python3 bot_daemon.py stop    - Остановить демон")
        print("  python3 bot_daemon.py status  - Показать статус")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        if daemon.start_daemon():
            try:
                # Держим демон работающим
                while daemon.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                daemon.stop_daemon()
        else:
            sys.exit(1)
    
    elif command == "stop":
        daemon.stop_daemon()
    
    elif command == "status":
        if daemon.is_bot_running():
            print("✅ Бот работает")
            print(f"📊 PID: {daemon.bot_process.pid}")
            print(f"🔄 Перезапусков: {daemon.restart_count}")
        else:
            print("❌ Бот не работает")
    
    else:
        print(f"❌ Неизвестная команда: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()











