#!/usr/bin/env python3
"""
Тест создания счета
"""

import asyncio
import logging
from bot_final import FastBot

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_invoice_creation():
    """Тестируем создание счета"""
    try:
        logger.info("🧪 Тестируем создание счета...")
        
        # Создаем экземпляр бота
        bot = FastBot()
        
        # Тестируем создание счета на 100 USDT
        amount = 100.0
        logger.info(f"💰 Создаем счет на {amount} USDT...")
        
        invoice_data = await bot.create_invoice(amount)
        
        if invoice_data:
            logger.info("✅ Счет создан успешно!")
            logger.info(f"📄 Данные счета:")
            logger.info(f"   ID: {invoice_data.get('invoice_id')}")
            logger.info(f"   URL: {invoice_data.get('pay_url')}")
            logger.info(f"   Сумма: {invoice_data.get('amount')}")
            logger.info(f"   Валюта: {invoice_data.get('asset')}")
            logger.info(f"   Статус: {invoice_data.get('status')}")
        else:
            logger.error("❌ Не удалось создать счет")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_invoice_creation())















