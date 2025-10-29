#!/usr/bin/env python3
"""
Интеграция с собственной платежной системой
"""

import asyncio
import aiohttp
import ssl
import logging
import hashlib
import hmac
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CustomPaymentAPI:
    """Класс для работы с собственной платежной системой"""
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        # Если URL не указан, используем переменную окружения или значение по умолчанию
        self.base_url = base_url or os.getenv('PAYMENT_SYSTEM_URL', 'https://api.your-payment-system.com')
        self.session = None
    
    async def __aenter__(self):
        # Создаем SSL контекст
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
    
    def _generate_signature(self, data: str) -> str:
        """Генерировать подпись для запроса"""
        return hmac.new(
            self.api_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _prepare_headers(self, data: dict) -> dict:
        """Подготовить заголовки с подписью"""
        data_str = json.dumps(data, sort_keys=True)
        signature = self._generate_signature(data_str)
        
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "X-Signature": signature,
            "X-Timestamp": str(int(datetime.now().timestamp()))
        }
    
    async def create_payment(self, amount: float, currency: str = "USDT", 
                           description: str = None, user_id: int = None) -> Optional[Dict[str, Any]]:
        """
        Создать платеж
        
        Args:
            amount: Сумма к оплате
            currency: Валюта (по умолчанию USDT)
            description: Описание платежа
            user_id: ID пользователя
            
        Returns:
            Словарь с данными платежа или None в случае ошибки
        """
        try:
            url = f"{self.base_url}/api/v1/payments/create"
            
            data = {
                "amount": amount,
                "currency": currency,
                "description": description or f"Пополнение баланса на {amount} {currency}",
                "user_id": user_id,
                "callback_url": f"{self.base_url}/api/v1/payments/callback",
                "success_url": "https://t.me/your_bot_username",
                "fail_url": "https://t.me/your_bot_username"
            }
            
            headers = self._prepare_headers(data)
            
            logger.info(f"📋 Создание платежа: {data}")
            
            async with self.session.post(url, headers=headers, json=data) as response:
                text = await response.text()
                logger.info(f"📊 Статус ответа: {response.status}")
                logger.info(f"📄 Ответ: {text}")
                
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        return result.get("data")
                    else:
                        logger.error(f"Ошибка создания платежа: {result.get('error')}")
                        return None
                else:
                    logger.error(f"HTTP ошибка: {response.status}")
                    logger.error(f"Ответ: {text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при создании платежа: {e}")
            return None
    
    async def get_payment_status(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить статус платежа
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Словарь со статусом платежа или None в случае ошибки
        """
        try:
            url = f"{self.base_url}/api/v1/payments/{payment_id}/status"
            
            data = {"payment_id": payment_id}
            headers = self._prepare_headers(data)
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        return result.get("data")
                    else:
                        logger.error(f"Ошибка получения статуса: {result.get('error')}")
                        return None
                else:
                    text = await response.text()
                    logger.error(f"HTTP ошибка: {response.status}")
                    logger.error(f"Ответ: {text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при получении статуса платежа: {e}")
            return None
    
    async def check_payment_status(self, payment_id: str) -> str:
        """
        Проверить статус платежа
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Статус платежа: 'paid', 'pending', 'failed' или 'error'
        """
        payment_data = await self.get_payment_status(payment_id)
        if payment_data:
            status = payment_data.get("status", "error")
            # Маппинг статусов на стандартные
            status_map = {
                "completed": "paid",
                "pending": "pending", 
                "failed": "failed",
                "cancelled": "failed",
                "expired": "failed"
            }
            return status_map.get(status, "error")
        return "error"
    
    async def get_payment_url(self, payment_id: str) -> Optional[str]:
        """
        Получить URL для оплаты
        
        Args:
            payment_id: ID платежа
            
        Returns:
            URL для оплаты или None в случае ошибки
        """
        payment_data = await self.get_payment_status(payment_id)
        if payment_data:
            return payment_data.get("payment_url")
        return None
    
    async def get_balance(self) -> Optional[Dict[str, Any]]:
        """
        Получить баланс системы
        
        Returns:
            Словарь с балансами или None в случае ошибки
        """
        try:
            url = f"{self.base_url}/api/v1/balance"
            
            data = {"timestamp": int(datetime.now().timestamp())}
            headers = self._prepare_headers(data)
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        return result.get("data")
                    else:
                        logger.error(f"Ошибка получения баланса: {result.get('error')}")
                        return None
                else:
                    logger.error(f"HTTP ошибка: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при получении баланса: {e}")
            return None
    
    async def process_webhook(self, webhook_data: dict) -> bool:
        """
        Обработать webhook от платежной системы
        
        Args:
            webhook_data: Данные webhook
            
        Returns:
            True если webhook обработан успешно
        """
        try:
            # Проверяем подпись webhook
            signature = webhook_data.get("signature")
            data = webhook_data.get("data", {})
            
            if not self._verify_webhook_signature(data, signature):
                logger.error("Неверная подпись webhook")
                return False
            
            # Обрабатываем данные платежа
            payment_id = data.get("payment_id")
            status = data.get("status")
            amount = data.get("amount")
            user_id = data.get("user_id")
            
            logger.info(f"📨 Webhook: {payment_id} - {status} - {amount}")
            
            # Здесь можно добавить логику обработки платежа
            # Например, обновление баланса пользователя в базе данных
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            return False
    
    def _verify_webhook_signature(self, data: dict, signature: str) -> bool:
        """Проверить подпись webhook"""
        try:
            data_str = json.dumps(data, sort_keys=True)
            expected_signature = self._generate_signature(data_str)
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Ошибка проверки подписи: {e}")
            return False

# Импортируем конфигурацию
try:
    from payment_config import CUSTOM_PAYMENT_API_KEY, PAYMENT_SYSTEM_URL
except ImportError:
    # Fallback значения
    CUSTOM_PAYMENT_API_KEY = "tO8RcgkEg3ie8CsGWni00d3YHGxjlr5ce6KNykJBbT0"
    PAYMENT_SYSTEM_URL = "https://your-payment-system.com"

async def create_payment(amount: float, currency: str = "USDT", description: str = None, user_id: int = None) -> Optional[Dict[str, Any]]:
    """Создать платеж"""
    if not CUSTOM_PAYMENT_API_KEY:
        logger.error("API ключ не установлен")
        return None
    
    async with CustomPaymentAPI(CUSTOM_PAYMENT_API_KEY, PAYMENT_SYSTEM_URL) as api:
        return await api.create_payment(amount, currency, description, user_id)

async def check_payment_status(payment_id: str) -> str:
    """Проверить статус платежа"""
    if not CUSTOM_PAYMENT_API_KEY:
        logger.error("API ключ не установлен")
        return "error"
    
    async with CustomPaymentAPI(CUSTOM_PAYMENT_API_KEY, PAYMENT_SYSTEM_URL) as api:
        return await api.check_payment_status(payment_id)

async def get_payment_url(payment_id: str) -> Optional[str]:
    """Получить URL для оплаты"""
    if not CUSTOM_PAYMENT_API_KEY:
        logger.error("API ключ не установлен")
        return None
    
    async with CustomPaymentAPI(CUSTOM_PAYMENT_API_KEY, PAYMENT_SYSTEM_URL) as api:
        return await api.get_payment_url(payment_id)

async def get_balance() -> Optional[Dict[str, Any]]:
    """Получить баланс системы"""
    if not CUSTOM_PAYMENT_API_KEY:
        logger.error("API ключ не установлен")
        return None
    
    async with CustomPaymentAPI(CUSTOM_PAYMENT_API_KEY, PAYMENT_SYSTEM_URL) as api:
        return await api.get_balance()

async def process_webhook(webhook_data: dict) -> bool:
    """Обработать webhook от платежной системы"""
    if not CUSTOM_PAYMENT_API_KEY:
        logger.error("API ключ не установлен")
        return False
    
    async with CustomPaymentAPI(CUSTOM_PAYMENT_API_KEY, PAYMENT_SYSTEM_URL) as api:
        return await api.process_webhook(webhook_data)
