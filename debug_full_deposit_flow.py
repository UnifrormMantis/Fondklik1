#!/usr/bin/env python3
"""
Полная отладка процесса создания депозита
"""

import asyncio
import logging
import aiohttp
import ssl
import sqlite3
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_PATH = 'bot_database.db'
CRYPTO_BOT_TOKEN = "469004:AAFOCI5N0HAQg3RbUKynaRO0cSzADVj0x8R"

async def test_create_invoice():
    """Тестируем создание инвойса"""
    try:
        logger.info("🔍 Тестируем создание инвойса...")
        
        amount = 100.0
        
        # Создаем SSL контекст
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            url = "https://pay.crypt.bot/api/createInvoice"
            headers = {
                "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
                "Content-Type": "application/json"
            }
            
            data = {
                "asset": "USDT",
                "amount": str(amount),
                "description": f"Пополнение баланса на {amount} USDT",
                "hidden_message": f"Платеж на сумму {amount} USDT",
                "paid_btn_name": "openBot",
                "paid_btn_url": "https://t.me/your_bot_username"
            }
            
            async with session.post(url, headers=headers, json=data) as response:
                response_text = await response.text()
                logger.info(f"📥 Ответ CryptoBot: {response.status} - {response_text}")
                
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        invoice_data = result.get("result")
                        logger.info("✅ Инвойс создан успешно!")
                        return invoice_data
                    else:
                        logger.error(f"❌ Ошибка API: {result.get('error')}")
                        return None
                else:
                    logger.error(f"❌ HTTP ошибка: {response.status}")
                    return None
                    
    except Exception as e:
        logger.error(f"❌ Исключение при создании инвойса: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_user_validation(user_id):
    """Тестируем валидацию пользователя"""
    try:
        logger.info(f"🔍 Тестируем валидацию пользователя {user_id}...")
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли пользователь в базе
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                logger.error(f"❌ Пользователь {user_id} не найден в базе данных")
                return False
            
            logger.info(f"✅ Пользователь {user_id} найден в базе")
            
            # Проверяем количество активных депозитов
            cursor.execute('''
                SELECT COUNT(*) FROM deposit_payments
                WHERE user_id = ? AND status = 'pending'
            ''', (user_id,))
            active_count = cursor.fetchone()[0]
            
            logger.info(f"📊 Активных депозитов: {active_count}")
            
            if active_count >= 10:
                logger.error(f"❌ У пользователя уже есть {active_count} активных вкладов")
                return False
            
            logger.info("✅ Валидация пользователя прошла успешно!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка валидации пользователя: {e}")
        return False

def test_create_transaction(user_id, amount, deposit_type, wallet_address, invoice_id):
    """Тестируем создание транзакции"""
    try:
        logger.info(f"🔍 Тестируем создание транзакции...")
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Устанавливаем время истечения через час
            expires_at = datetime.now() + timedelta(hours=1)
            
            cursor.execute('''
                INSERT INTO user_transactions
                (user_id, amount, deposit_type, status, wallet_address, invoice_id, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, deposit_type, 'pending', wallet_address, invoice_id, expires_at))
            
            transaction_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"✅ Транзакция создана с ID: {transaction_id}")
            return transaction_id
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания транзакции: {e}")
        return None

async def main():
    logger.info("🧪 Полная отладка процесса создания депозита")
    
    # Тестируем с пользователем 798427688
    test_user_id = 798427688
    test_amount = 100.0
    test_deposit_type = '30_days'
    test_wallet_address = 'TTest123456789012345678901234567890'
    
    logger.info(f"👤 Тестируем с пользователем {test_user_id}")
    
    # 1. Тестируем валидацию пользователя
    if not test_user_validation(test_user_id):
        logger.error("❌ Валидация пользователя не прошла")
        return
    
    # 2. Тестируем создание инвойса
    invoice_data = await test_create_invoice()
    if not invoice_data:
        logger.error("❌ Создание инвойса не прошло")
        return
    
    # 3. Тестируем создание транзакции
    transaction_id = test_create_transaction(
        test_user_id, test_amount, test_deposit_type, 
        test_wallet_address, invoice_data.get('invoice_id')
    )
    if not transaction_id:
        logger.error("❌ Создание транзакции не прошло")
        return
    
    logger.info("✅ Все тесты прошли успешно!")
    logger.info(f"📄 Данные для создания депозита:")
    logger.info(f"   User ID: {test_user_id}")
    logger.info(f"   Amount: {test_amount}")
    logger.info(f"   Deposit Type: {test_deposit_type}")
    logger.info(f"   Wallet: {test_wallet_address}")
    logger.info(f"   Invoice ID: {invoice_data.get('invoice_id')}")
    logger.info(f"   Pay URL: {invoice_data.get('pay_url')}")
    logger.info(f"   Transaction ID: {transaction_id}")

if __name__ == "__main__":
    asyncio.run(main())















