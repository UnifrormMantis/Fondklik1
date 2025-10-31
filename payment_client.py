#!/usr/bin/env python3
"""
Клиент для работы с Payment Bot API
Интегрирован в основной бот ФондКлик
"""

import requests
import logging
import os
from typing import Dict, Optional, Any
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

logger = logging.getLogger(__name__)

# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================

# Настройки Payment Bot API
PAYMENT_API_KEY = os.getenv("PAYMENT_API_KEY", "rsG7Hzt0EaEY5ZoEH4eE96SiY234qpiSYg5d92xrSm4")

# URL для Payment API (если задан, используется вместо автопоиска)
PAYMENT_API_URL = os.getenv("PAYMENT_API_URL")

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
    
    # Если задан Payment API URL, используем его
    if PAYMENT_API_URL:
        _cached_api_url = PAYMENT_API_URL
        logger.info(f"✅ Используется Payment API: {PAYMENT_API_URL}")
        return PAYMENT_API_URL
    
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
        # Сначала пробуем переменную окружения
        payment_api_url = os.getenv("PAYMENT_API_URL")
        if payment_api_url:
            self.api_url = payment_api_url
            logger.info(f"✅ Используется Payment API из переменной окружения: {payment_api_url}")
        else:
            # Если нет переменной - ищем на портах
            self.api_url = find_payment_bot()
            if not self.api_url:
                logger.warning("⚠️ Payment API URL не найден при инициализации. Будет попытка найти при первом вызове.")
    
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
        """Получить активный кошелек для приема платежей (DEPRECATED - используйте get_payment_wallet)"""
        # Перенаправляем на новый метод
        logger.warning("Используется устаревший метод get_active_wallet. Используйте get_payment_wallet(user_wallet)")
        return self.get_payment_wallet("system")

    def get_payment_wallet(self, user_wallet: str) -> Dict[str, Any]:
        """Получить кошелек для приема платежей"""
        global _cached_api_url
        
        # Всегда проверяем переменную окружения заново (на случай если она изменилась)
        payment_api_url = os.getenv("PAYMENT_API_URL")
        
        # Если API URL не найден, попробуем найти заново
        if not self.api_url:
            # Сначала пробуем переменную окружения
            if payment_api_url:
                self.api_url = payment_api_url
                logger.info(f"✅ Используется Payment API из переменной окружения: {payment_api_url}")
            else:
                # Ищем на портах
                self.api_url = find_payment_bot()
            if not self.api_url:
                logger.error("❌ Payment Bot не найден и переменная PAYMENT_API_URL не установлена")
                return {"success": False, "error": "Payment Bot не найден"}
        
        # Если есть переменная окружения и она отличается - используем её
        if payment_api_url and self.api_url != payment_api_url:
            logger.info(f"✅ Обновляем Payment API URL на: {payment_api_url}")
            self.api_url = payment_api_url
        
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
    
    def check_payment(self, user_id: int, user_wallet: str) -> Dict[str, Any]:
        """Проверить платеж от пользователя (упрощенный метод для бота)
        
        Возвращает первый найденный валидный платеж, который:
        - Отправлен с кошелька пользователя
        - Это USDT (не TRON)
        - Не меньше 50 USDT
        - Поступил на активный кошелек
        """
        try:
            result = self.check_user_payments(user_wallet)
            
            if not result.get("success"):
                return {
                    "success": False,
                    "payment_found": False,
                    "error": result.get("error", "Unknown error")
                }
            
            payments = result.get("payments", [])
            
            if not payments:
                return {
                    "success": True,
                    "payment_found": False,
                    "message": "Платеж еще не поступил"
                }
            
            # Возвращаем первый валидный платеж (самый новый)
            payment = payments[0]
            
            return {
                "success": True,
                "payment_found": True,
                "amount": payment.get("amount", 0),
                "tx_hash": payment.get("tx_hash", ""),
                "confirmed": payment.get("confirmed", False)
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки платежа: {e}", exc_info=True)
            return {
                "success": False,
                "payment_found": False,
                "error": str(e)
            }

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
