#!/usr/bin/env python3
"""
Клиент для работы с Payment Bot API
Интегрирован в основной бот ФондКлик
"""

import requests
import logging
import os
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================

# Настройки Payment Bot API
PAYMENT_API_KEY = os.getenv("PAYMENT_API_KEY", "rsG7Hzt0EaEY5ZoEH4eE96SiY234qpiSYg5d92xrSm4")

# URL для Railway (если задан, используется вместо автопоиска)
RAILWAY_PAYMENT_API_URL = os.getenv("PAYMENT_API_URL")

# Порты для автоматического поиска Payment Bot (локально)
PAYMENT_PORTS = [8000, 8001, 8002, 8003, 8004, 8005, 3000, 3001, 5000, 5001]

# Кэш для найденного URL
_cached_api_url = None

# =============================================================================
# КЛИЕНТ ДЛЯ РАБОТЫ С PAYMENT BOT API
# =============================================================================

def find_payment_bot():
    """Автоматически найти Payment Bot на доступных портах"""
    global _cached_api_url
    
    # Если уже нашли, возвращаем кэшированный URL
    if _cached_api_url:
        return _cached_api_url
    
    # Если задан Railway URL, используем его
    if RAILWAY_PAYMENT_API_URL:
        _cached_api_url = RAILWAY_PAYMENT_API_URL
        logger.info(f"✅ Используется Railway Payment API: {RAILWAY_PAYMENT_API_URL}")
        return RAILWAY_PAYMENT_API_URL
    
    logger.info("🔍 Поиск Payment Bot на доступных портах...")
    
    for port in PAYMENT_PORTS:
        test_url = f"http://localhost:{port}"
        try:
            # Пробуем подключиться к /get-payment-wallet
            response = requests.post(
                f"{test_url}/get-payment-wallet",
                headers={'X-API-Key': PAYMENT_API_KEY, 'Content-Type': 'application/json'},
                json={'user_wallet': 'test'},
                timeout=2
            )
            
            if response.status_code == 200:
                _cached_api_url = test_url
                logger.info(f"✅ Payment Bot найден на порту {port}: {test_url}")
                return test_url
                
        except Exception as e:
            logger.debug(f"Порт {port} недоступен: {e}")
            continue
    
    logger.warning("❌ Payment Bot не найден ни на одном из портов")
    return None

class PaymentClient:
    def __init__(self):
        self.api_key = PAYMENT_API_KEY
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        self.api_url = find_payment_bot()
    
    def verify_payment(self, wallet_address: str, amount: float, currency: str = "USDT") -> Dict[str, Any]:
        """Проверить платеж на кошелек"""
        try:
            response = requests.post(
                f"{self.api_url}/verify-payment",
                headers=self.headers,
                json={
                    "wallet_address": wallet_address,
                    "user_wallet": wallet_address,  # Добавляем user_wallet
                    "expected_amount": amount,      # Изменяем amount на expected_amount
                    "amount": amount,               # Оставляем amount для совместимости
                    "currency": currency
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка проверки платежа: {response.status_code} - {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Payment API: {e}")
            return {"success": False, "error": str(e)}
    
    def get_active_wallet(self) -> Dict[str, Any]:
        """Получить активный кошелек для приема платежей"""
        try:
            response = requests.get(
                f"{self.api_url}/active-wallet",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения активного кошелька: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Payment API: {e}")
            return {"success": False, "error": str(e)}

    def get_payment_wallet(self, user_wallet: str) -> Dict[str, Any]:
        """Получить кошелек для приема платежей"""
        global _cached_api_url
        
        # Если API URL не найден, попробуем найти заново
        if not self.api_url:
            self.api_url = find_payment_bot()
            if not self.api_url:
                return {"success": False, "error": "Payment Bot не найден"}
        
        try:
            response = requests.post(
                f"{self.api_url}/get-payment-wallet",
                headers=self.headers,
                json={'user_wallet': user_wallet},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения кошелька для платежа: {response.status_code}")
                # Попробуем найти Payment Bot на другом порту
                _cached_api_url = None
                self.api_url = find_payment_bot()
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Payment API: {e}")
            # Попробуем найти Payment Bot на другом порту
            _cached_api_url = None
            self.api_url = find_payment_bot()
            return {"success": False, "error": str(e)}

    def check_user_payments(self, user_wallet: str) -> Dict[str, Any]:
        """Проверить переводы с кошелька пользователя"""
        try:
            response = requests.post(
                f"{self.api_url}/check-user-payments",
                headers=self.headers,
                json={"user_wallet": user_wallet},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка проверки переводов пользователя: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Payment API: {e}")
            return {"success": False, "error": str(e)}

    def get_wallet_info(self, wallet_address: str) -> Dict[str, Any]:
        """Получить информацию о кошельке"""
        try:
            response = requests.get(
                f"{self.api_url}/wallet-info",
                headers=self.headers,
                params={"wallet_address": wallet_address},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения информации о кошельке: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Payment API: {e}")
            return {"success": False, "error": str(e)}
    
    def check_payment_status(self, wallet_address: str, amount: float) -> bool:
        """Проверить статус платежа (упрощенная версия)"""
        result = self.verify_payment(wallet_address, amount)
        return result.get("success", False) and result.get("confirmed", False)
    
    def test_connection(self) -> bool:
        """Тестировать соединение с Payment Bot API"""
        try:
            response = requests.get(
                f"{self.api_url}/health",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

# Глобальный экземпляр клиента
payment_client = PaymentClient()
