#!/usr/bin/env python3
"""
Тест создания счета через CryptoBot API
"""

import asyncio
import aiohttp
import ssl
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_create_invoice():
    """Тест создания счета"""
    
    token = "469004:AAFOCI5N0HAQg3RbUKynaRO0cSzADVj0x8R"
    base_url = "https://pay.crypt.bot/api"
    
    # Создаем SSL контекст
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Создаем коннектор
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        try:
            # Тестируем создание счета
            url = f"{base_url}/createInvoice"
            headers = {
                "Crypto-Pay-API-Token": token,
                "Content-Type": "application/json"
            }
            
            data = {
                "asset": "USDT",
                "amount": "1.0",
                "description": "Тестовый платеж",
                "hidden_message": "Тест создания счета",
                "paid_btn_name": "openBot",
                "paid_btn_url": "https://t.me/your_bot_username"
            }
            
            print("🔍 Тестируем создание счета...")
            print(f"📋 Данные: {data}")
            
            async with session.post(url, headers=headers, json=data) as response:
                print(f"📊 Статус ответа: {response.status}")
                
                text = await response.text()
                print(f"📄 Ответ: {text}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Успешное создание счета!")
                    print(f"📋 Результат: {result}")
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_create_invoice())
