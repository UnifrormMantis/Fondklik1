#!/usr/bin/env python3
"""
Интеграция с CryptoBot API для обработки платежей
"""

import asyncio
import aiohttp
import ssl
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CryptoBotAPI:
    """Класс для работы с CryptoBot API"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://pay.crypt.bot/api"
        self.session = None
    
    async def __aenter__(self):
        # Создаем SSL контекст с отключенной проверкой сертификатов
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Создаем коннектор с SSL настройками
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        # Создаем сессию с таймаутами
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_invoice(self, amount: float, currency: str = "USDT", 
                           description: str = None) -> Optional[Dict[str, Any]]:
        """
        Создать счет для оплаты
        
        Args:
            amount: Сумма к оплате
            currency: Валюта (по умолчанию USDT)
            description: Описание платежа
            
        Returns:
            Словарь с данными счета или None в случае ошибки
        """
        try:
            url = f"{self.base_url}/createInvoice"
            headers = {
                "Crypto-Pay-API-Token": self.token,
                "Content-Type": "application/json"
            }
            
            # Используем POST с JSON данными
            data = {
                "asset": currency,
                "amount": str(amount),
                "description": description or f"Пополнение баланса на {amount} {currency}",
                "hidden_message": f"Платеж на сумму {amount} {currency}",
                "paid_btn_name": "openBot",
                "paid_btn_url": "https://t.me/your_bot_username"
            }
            
            logger.info(f"📋 Отправляем данные: {data}")
            
            async with self.session.post(url, headers=headers, json=data) as response:
                text = await response.text()
                logger.info(f"📊 Статус ответа: {response.status}")
                logger.info(f"📄 Ответ: {text}")
                
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        return result.get("result")
                    else:
                        logger.error(f"Ошибка создания счета: {result.get('error')}")
                        return None
                else:
                    logger.error(f"HTTP ошибка: {response.status}")
                    logger.error(f"Ответ: {text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при создании счета: {e}")
            return None
    
    async def get_invoice_status(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить статус счета
        
        Args:
            invoice_id: ID счета
            
        Returns:
            Словарь со статусом счета или None в случае ошибки
        """
        try:
            url = f"{self.base_url}/getInvoices"
            headers = {
                "Crypto-Pay-API-Token": self.token
            }
            
            params = {
                "invoice_ids": invoice_id
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok") and result.get("result", {}).get("items"):
                        return result["result"]["items"][0]
                    else:
                        logger.error(f"Ошибка получения статуса счета: {result.get('error')}")
                        return None
                else:
                    text = await response.text()
                    logger.error(f"HTTP ошибка: {response.status}")
                    logger.error(f"Ответ: {text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при получении статуса счета: {e}")
            return None
    
    async def check_payment_status(self, invoice_id: str) -> str:
        """
        Проверить статус платежа
        
        Args:
            invoice_id: ID счета
            
        Returns:
            Статус платежа: 'paid', 'active', 'expired' или 'error'
        """
        invoice_data = await self.get_invoice_status(invoice_id)
        if invoice_data:
            return invoice_data.get("status", "error")
        return "error"
    
    async def get_balance(self) -> Optional[Dict[str, Any]]:
        """
        Получить баланс CryptoBot
        
        Returns:
            Словарь с балансами или None в случае ошибки
        """
        try:
            url = f"{self.base_url}/getBalance"
            headers = {
                "Crypto-Pay-API-Token": self.token
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        return result.get("result")
                    else:
                        logger.error(f"Ошибка получения баланса: {result.get('error')}")
                        return None
                else:
                    logger.error(f"HTTP ошибка: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {e}")
            return None

# Глобальная переменная для токена (будет установлена из конфигурации)
CRYPTO_BOT_TOKEN = "469004:AAFOCI5N0HAQg3RbUKynaRO0cSzADVj0x8R"

async def create_invoice(amount: float, currency: str = "USDT", description: str = None) -> Optional[Dict[str, Any]]:
    """Создать счет для оплаты"""
    if not CRYPTO_BOT_TOKEN:
        logger.error("CryptoBot токен не установлен")
        return None
    
    async with CryptoBotAPI(CRYPTO_BOT_TOKEN) as api:
        return await api.create_invoice(amount, currency, description)

async def check_payment_status(invoice_id: str) -> str:
    """Проверить статус платежа"""
    if not CRYPTO_BOT_TOKEN:
        logger.error("CryptoBot токен не установлен")
        return "error"
    
    async with CryptoBotAPI(CRYPTO_BOT_TOKEN) as api:
        return await api.check_payment_status(invoice_id)

async def get_balance() -> Optional[Dict[str, Any]]:
    """Получить баланс CryptoBot"""
    if not CRYPTO_BOT_TOKEN:
        logger.error("CryptoBot токен не установлен")
        return None
    
    async with CryptoBotAPI(CRYPTO_BOT_TOKEN) as api:
        return await api.get_balance()
