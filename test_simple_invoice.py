#!/usr/bin/env python3
"""
Простой тест создания счета
"""

import asyncio
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def create_fake_invoice(amount: float):
    """Создать фиктивный счет"""
    try:
        logger.info("⚠️ CryptoBot API временно отключен - используем заглушку")
        
        # Создаем фиктивный счет для тестирования
        fake_invoice_id = f"fake_{int(time.time())}_{amount}"
        
        result = {
            "invoice_id": fake_invoice_id,
            "pay_url": f"https://t.me/cryptobot?start=pay_{fake_invoice_id}",
            "amount": str(amount),
            "asset": "USDT",
            "status": "active"
        }
        
        logger.info("✅ Фиктивный счет создан успешно!")
        logger.info(f"📄 Данные счета:")
        logger.info(f"   ID: {result.get('invoice_id')}")
        logger.info(f"   URL: {result.get('pay_url')}")
        logger.info(f"   Сумма: {result.get('amount')}")
        logger.info(f"   Валюта: {result.get('asset')}")
        logger.info(f"   Статус: {result.get('status')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании фиктивного счета: {e}")
        return None

async def main():
    logger.info("🧪 Тестируем создание фиктивного счета...")
    
    # Тестируем создание счета на 100 USDT
    amount = 100.0
    logger.info(f"💰 Создаем счет на {amount} USDT...")
    
    invoice_data = await create_fake_invoice(amount)
    
    if invoice_data:
        logger.info("✅ Тест прошел успешно!")
    else:
        logger.error("❌ Тест не прошел!")

if __name__ == "__main__":
    asyncio.run(main())















