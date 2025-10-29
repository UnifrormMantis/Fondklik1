#!/usr/bin/env python3
"""
Клиент для интеграции с Payment Bot API
"""

import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PaymentClient:
    """Клиент для работы с Payment Bot API"""
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:8001"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def get_payment_wallet(self, user_wallet: str) -> Dict[str, Any]:
        """Получить активный кошелек для приема платежей"""
        try:
            response = requests.post(
                f"{self.base_url}/get-payment-wallet",
                headers=self.headers,
                json={"user_wallet": user_wallet},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения кошелька: {e}")
            return {"success": False, "error": str(e)}
    
    def check_user_payments(self, user_wallet: str) -> Dict[str, Any]:
        """Проверить платежи пользователя"""
        try:
            response = requests.post(
                f"{self.base_url}/check-user-payments",
                headers=self.headers,
                json={"user_wallet": user_wallet},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка проверки платежей: {e}")
            return {"success": False, "error": str(e)}






