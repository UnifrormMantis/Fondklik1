#!/usr/bin/env python3
"""
Тест CryptoBot API
"""

import aiohttp
import asyncio
import ssl
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CRYPTO_BOT_TOKEN = "469004:AAFOCI5N0HAQg3RbUKynaRO0cSzADVj0x8R"

async def test_crypto_bot_api():
    """Тестируем CryptoBot API"""
    try:
        # Создаем SSL контекст
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Тестируем создание инвойса
            url = "https://pay.crypt.bot/api/createInvoice"
            headers = {
                "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
                "Content-Type": "application/json"
            }
            
            data = {
                "asset": "USDT",
                "amount": "10.0",
                "description": "Test invoice"
            }
            
            logger.info("🔍 Тестируем создание инвойса...")
            logger.info(f"URL: {url}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Data: {data}")
            
            async with session.post(url, headers=headers, json=data) as response:
                response_text = await response.text()
                logger.info(f"Status: {response.status}")
                logger.info(f"Response: {response_text}")
                
                if response.status == 200:
                    logger.info("✅ CryptoBot API работает!")
                    return True
                else:
                    logger.error(f"❌ CryptoBot API вернул ошибку: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании CryptoBot API: {e}")
        return False

async def test_get_me():
    """Тестируем метод getMe"""
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            url = "https://pay.crypt.bot/api/getMe"
            headers = {
                "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
                "Content-Type": "application/json"
            }
            
            logger.info("🔍 Тестируем getMe...")
            
            async with session.get(url, headers=headers) as response:
                response_text = await response.text()
                logger.info(f"Status: {response.status}")
                logger.info(f"Response: {response_text}")
                
                if response.status == 200:
                    logger.info("✅ getMe работает!")
                    return True
                else:
                    logger.error(f"❌ getMe вернул ошибку: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании getMe: {e}")
        return False

async def main():
    logger.info("🧪 Тестируем CryptoBot API")
    
    # Тестируем getMe
    logger.info("\n1️⃣ Тестируем getMe...")
    getme_result = await test_get_me()
    
    # Тестируем создание инвойса
    logger.info("\n2️⃣ Тестируем создание инвойса...")
    invoice_result = await test_crypto_bot_api()
    
    if getme_result and invoice_result:
        logger.info("\n✅ Все тесты прошли успешно!")
    else:
        logger.info("\n❌ Некоторые тесты не прошли!")

if __name__ == "__main__":
    asyncio.run(main())
