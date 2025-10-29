#!/usr/bin/env python3
"""
HTTP сервер для обработки webhook от платежной системы
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebhookHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов для webhook"""
    
    def __init__(self, bot_instance, *args, **kwargs):
        self.bot = bot_instance
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """Обработка POST запросов от платежной системы"""
        try:
            # Получаем длину контента
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Читаем данные
            post_data = self.rfile.read(content_length)
            
            # Парсим JSON
            try:
                webhook_data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                self.send_error_response(400, "Invalid JSON")
                return
            
            logger.info(f"Получен webhook: {webhook_data}")
            
            # Обрабатываем платеж через бота
            result = self.bot.process_payment_webhook(webhook_data)
            
            if result.get("success"):
                self.send_success_response(result)
            else:
                self.send_error_response(400, result.get("message", "Unknown error"))
                
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            self.send_error_response(500, f"Internal error: {str(e)}")
    
    def do_GET(self):
        """Обработка GET запросов (для проверки статуса)"""
        if self.path == '/health':
            self.send_success_response({"status": "ok", "message": "Webhook server is running"})
        else:
            self.send_error_response(404, "Not found")
    
    def send_success_response(self, data):
        """Отправить успешный ответ"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))
        logger.info(f"Отправлен успешный ответ: {data}")
    
    def send_error_response(self, code, message):
        """Отправить ответ об ошибке"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps({"error": message}, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))
        logger.error(f"Отправлен ответ об ошибке {code}: {message}")
    
    def log_message(self, format, *args):
        """Отключить стандартное логирование HTTP запросов"""
        pass

def create_webhook_handler(bot_instance):
    """Создать обработчик webhook с доступом к экземпляру бота"""
    def handler(*args, **kwargs):
        return WebhookHandler(bot_instance, *args, **kwargs)
    return handler

class WebhookServer:
    """HTTP сервер для обработки webhook"""
    
    def __init__(self, bot_instance, host='localhost', port=8001):
        self.bot = bot_instance
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Запустить webhook сервер"""
        try:
            handler = create_webhook_handler(self.bot)
            self.server = HTTPServer((self.host, self.port), handler)
            
            logger.info(f"🚀 Webhook сервер запущен на {self.host}:{self.port}")
            logger.info(f"📡 Endpoint для платежей: http://{self.host}:{self.port}/")
            logger.info(f"🏥 Health check: http://{self.host}:{self.port}/health")
            
            # Запускаем сервер в отдельном потоке
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска webhook сервера: {e}")
            return False
    
    def stop(self):
        """Остановить webhook сервер"""
        if self.server:
            logger.info("🛑 Остановка webhook сервера...")
            self.server.shutdown()
            self.server.server_close()
            if self.thread:
                self.thread.join(timeout=5)
            logger.info("✅ Webhook сервер остановлен")

def test_webhook():
    """Тест webhook сервера"""
    print("🧪 Тестирование webhook сервера")
    print("=" * 40)
    
    # Импортируем бота
    from bot_final import FastBot
    
    # Создаем экземпляр бота
    bot = FastBot()
    
    # Создаем и запускаем webhook сервер
    webhook_server = WebhookServer(bot, host='localhost', port=8001)
    
    if webhook_server.start():
        print("✅ Webhook сервер запущен")
        print("📡 Endpoint: http://localhost:8001/")
        print("🏥 Health check: http://localhost:8001/health")
        print()
        print("📋 Пример webhook данных:")
        print(json.dumps({
            "user_wallet": "TTestUser1234567890123456789012345",
            "amount": 100.5,
            "transaction_hash": "abc123...",
            "confirmed_at": "2025-10-06T15:00:00Z"
        }, indent=2))
        print()
        print("💡 Для тестирования отправьте POST запрос с JSON данными")
        print("🛑 Нажмите Ctrl+C для остановки")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Остановка...")
            webhook_server.stop()
            print("✅ Тест завершен")
    else:
        print("❌ Ошибка запуска webhook сервера")

if __name__ == "__main__":
    test_webhook()










