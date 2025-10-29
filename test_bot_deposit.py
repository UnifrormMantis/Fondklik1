#!/usr/bin/env python3
"""
Тест создания депозита через бота
"""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock
from bot_final import FastBot

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_deposit_creation():
    """Тестируем создание депозита"""
    try:
        logger.info("🧪 Тестируем создание депозита через бота...")
        
        # Создаем экземпляр бота
        bot = FastBot()
        
        # Тестируем создание инвойса
        amount = 100.0
        logger.info(f"💰 Создаем инвойс на {amount} USDT...")
        
        invoice_data = await bot.create_invoice(amount)
        
        if invoice_data:
            logger.info("✅ Инвойс создан успешно!")
            logger.info(f"📄 Данные инвойса:")
            logger.info(f"   Invoice ID: {invoice_data.get('invoice_id')}")
            logger.info(f"   Pay URL: {invoice_data.get('pay_url')}")
            logger.info(f"   Amount: {invoice_data.get('amount')}")
            logger.info(f"   Asset: {invoice_data.get('asset')}")
            logger.info(f"   Status: {invoice_data.get('status')}")
        else:
            logger.error("❌ Не удалось создать инвойс")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_deposit_creation())















