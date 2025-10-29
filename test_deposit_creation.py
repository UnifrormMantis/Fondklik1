#!/usr/bin/env python3
"""
Тест создания депозита с детальной диагностикой
"""

import asyncio
import logging
import aiohttp
import ssl

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
            
            logger.info(f"📤 Отправляем запрос:")
            logger.info(f"   URL: {url}")
            logger.info(f"   Headers: {headers}")
            logger.info(f"   Data: {data}")
            
            async with session.post(url, headers=headers, json=data) as response:
                response_text = await response.text()
                logger.info(f"📥 Получен ответ:")
                logger.info(f"   Status: {response.status}")
                logger.info(f"   Response: {response_text}")
                
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        invoice_data = result.get("result")
                        logger.info("✅ Инвойс создан успешно!")
                        logger.info(f"   Invoice ID: {invoice_data.get('invoice_id')}")
                        logger.info(f"   Pay URL: {invoice_data.get('pay_url')}")
                        logger.info(f"   Amount: {invoice_data.get('amount')}")
                        logger.info(f"   Asset: {invoice_data.get('asset')}")
                        logger.info(f"   Status: {invoice_data.get('status')}")
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

async def main():
    logger.info("🧪 Тестируем создание депозита с детальной диагностикой")
    
    # Тестируем создание инвойса
    invoice_data = await test_create_invoice()
    
    if invoice_data:
        logger.info("✅ Тест прошел успешно!")
    else:
        logger.error("❌ Тест не прошел!")

if __name__ == "__main__":
    asyncio.run(main())















