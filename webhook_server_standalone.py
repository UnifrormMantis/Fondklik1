#!/usr/bin/env python3
"""
Автономный HTTP сервер для обработки webhook от платежной системы
"""

import json
import logging
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
DATABASE_PATH = "bot_database.db"

class WebhookHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов для webhook"""
    
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
            
            # Обрабатываем платеж
            result = self.process_payment_webhook(webhook_data)
            
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
    
    def process_payment_webhook(self, webhook_data: dict):
        """Обработать webhook от платежной системы о получении платежа"""
        try:
            user_wallet = webhook_data.get('user_wallet')
            received_amount = webhook_data.get('amount', 0)
            transaction_hash = webhook_data.get('transaction_hash', '')
            confirmed_at = webhook_data.get('confirmed_at', '')
            
            logger.info(f"Получен webhook о платеже: {received_amount} USDT от {user_wallet}")
            
            # Ищем пользователя по кошельку
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Ищем пользователя с таким кошельком
                cursor.execute('''
                    SELECT telegram_id, wallet_address FROM users 
                    WHERE wallet_address = ?
                ''', (user_wallet,))
                
                user_result = cursor.fetchone()
                
                if user_result:
                    user_id, wallet_address = user_result
                    logger.info(f"Найден пользователь {user_id} с кошельком {wallet_address}")
                    
                    # Создаем транзакцию
                    transaction_id = self.create_user_transaction(
                        cursor, user_id, received_amount, '10_days', user_wallet
                    )
                    
                    # Обновляем баланс пользователя
                    self.update_user_balance(cursor, user_id, received_amount, transaction_id)
                    
                    conn.commit()
                    
                    logger.info(f"✅ Платеж обработан: {received_amount} USDT для пользователя {user_id}")
                    
                    return {
                        "success": True,
                        "message": f"Платеж обработан: {received_amount} USDT",
                        "transaction_id": transaction_id
                    }
                else:
                    logger.warning(f"Пользователь с кошельком {user_wallet} не найден")
                    return {
                        "success": False,
                        "message": "Пользователь не найден"
                    }
                    
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            return {
                "success": False,
                "message": f"Ошибка обработки: {str(e)}"
            }
    
    def create_user_transaction(self, cursor, user_id: int, amount: float, deposit_type: str, wallet_address: str):
        """Создать транзакцию пользователя"""
        try:
            cursor.execute('''
                INSERT INTO user_transactions 
                (user_id, amount, deposit_type, status, wallet_address, invoice_id, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                amount,
                deposit_type,
                'completed',
                wallet_address,
                f"webhook_{user_id}_{int(datetime.now().timestamp())}",
                datetime.now().timestamp() + 86400  # 24 часа
            ))
            
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Ошибка создания транзакции: {e}")
            return None
    
    def update_user_balance(self, cursor, user_id: int, amount: float, transaction_id: int):
        """Обновить баланс пользователя"""
        try:
            # Обновляем баланс
            cursor.execute('''
                UPDATE users 
                SET balance = balance + ? 
                WHERE telegram_id = ?
            ''', (amount, user_id))
            
            # Создаем запись в deposit_payments
            cursor.execute('''
                INSERT INTO deposit_payments 
                (user_id, original_amount, return_amount, days_remaining, status, created_at, payment_date, deposit_type, wallet_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                amount,
                amount * 1.08,  # 8% прибыль для 10-дневного депозита
                10,  # 10 дней
                'pending',
                datetime.now(),
                datetime.now(),
                '10_days',
                ''  # wallet_address будет заполнен позже
            ))
            
            logger.info(f"Баланс пользователя {user_id} увеличен на {amount} USDT")
            
        except Exception as e:
            logger.error(f"Ошибка обновления баланса: {e}")
    
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

class WebhookServer:
    """HTTP сервер для обработки webhook"""
    
    def __init__(self, host='localhost', port=8001):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Запустить webhook сервер"""
        try:
            self.server = HTTPServer((self.host, self.port), WebhookHandler)
            
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

def main():
    """Основная функция"""
    print("🚀 Запуск автономного webhook сервера")
    print("=" * 40)
    
    # Создаем и запускаем webhook сервер
    webhook_server = WebhookServer(host='localhost', port=8001)
    
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
            print("✅ Webhook сервер остановлен")
    else:
        print("❌ Ошибка запуска webhook сервера")

if __name__ == "__main__":
    main()










