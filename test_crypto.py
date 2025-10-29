#!/usr/bin/env python3
"""
Тест CryptoBot API
"""

import asyncio
import aiohttp
import ssl
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_crypto_bot():
    """Тест подключения к CryptoBot API"""
    
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
            # Тестируем получение баланса
            url = f"{base_url}/getBalance"
            headers = {
                "Crypto-Pay-API-Token": token
            }
            
            print("🔍 Тестируем подключение к CryptoBot API...")
            async with session.get(url, headers=headers) as response:
                print(f"📊 Статус ответа: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Успешное подключение!")
                    print(f"📋 Ответ: {result}")
                    
                    if result.get("ok"):
                        print("🎉 API токен работает корректно!")
                        balance = result.get("result", [])
                        print(f"💰 Баланс: {balance}")
                    else:
                        print(f"❌ Ошибка API: {result.get('error')}")
                else:
                    text = await response.text()
                    print(f"❌ HTTP ошибка: {response.status}")
                    print(f"📄 Ответ: {text}")
                    
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    asyncio.run(test_crypto_bot())

















