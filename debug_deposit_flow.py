#!/usr/bin/env python3
"""
Отладка процесса создания депозита
"""

import sqlite3
import logging
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_PATH = 'bot_database.db'

def test_database_connection():
    """Тестируем подключение к базе данных"""
    try:
        logger.info("🔍 Тестируем подключение к базе данных...")
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            logger.info(f"✅ База данных работает. Пользователей: {count}")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def test_user_transaction_creation():
    """Тестируем создание транзакции"""
    try:
        logger.info("🔍 Тестируем создание транзакции...")
        
        test_user_id = 123456789
        test_amount = 100.0
        test_deposit_type = '30_days'
        test_wallet_address = 'TTest123456789012345678901234567890'
        test_invoice_id = 'test_invoice_123'
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Устанавливаем время истечения через час
            expires_at = datetime.now() + timedelta(hours=1)
            
            cursor.execute('''
                INSERT INTO user_transactions
                (user_id, amount, deposit_type, status, wallet_address, invoice_id, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (test_user_id, test_amount, test_deposit_type, 'pending', test_wallet_address, test_invoice_id, expires_at))
            
            transaction_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"✅ Транзакция создана с ID: {transaction_id}")
            
            # Удаляем тестовую транзакцию
            cursor.execute('DELETE FROM user_transactions WHERE id = ?', (transaction_id,))
            conn.commit()
            logger.info("🗑️ Тестовая транзакция удалена")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания транзакции: {e}")
        return False

def test_user_exists():
    """Проверяем, есть ли тестовый пользователь"""
    try:
        logger.info("🔍 Проверяем наличие тестового пользователя...")
        
        test_user_id = 123456789
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (test_user_id,))
            user = cursor.fetchone()
            
            if user:
                logger.info(f"✅ Пользователь {test_user_id} найден: {user}")
            else:
                logger.info(f"ℹ️ Пользователь {test_user_id} не найден - это нормально для теста")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки пользователя: {e}")
        return False

def main():
    logger.info("🧪 Отладка процесса создания депозита")
    
    # Тестируем подключение к базе данных
    if not test_database_connection():
        return
    
    # Проверяем пользователя
    test_user_exists()
    
    # Тестируем создание транзакции
    if test_user_transaction_creation():
        logger.info("✅ Все тесты прошли успешно!")
    else:
        logger.error("❌ Тесты не прошли!")

if __name__ == "__main__":
    main()















