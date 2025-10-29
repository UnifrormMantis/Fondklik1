#!/usr/bin/env python3
"""
Конфигурация платежной системы
"""

# API ключ для проверки USDT платежей
USDT_PAYMENT_API_KEY = "QteR2mHB_hX7BLQAedfgXRWRcGiHsTR6HFtvMqaA-uQ"

# URL системы проверки платежей
PAYMENT_VERIFICATION_URL = "http://localhost:8002"

# Кошелек для приема платежей
PAYMENT_WALLET = "TWJ5wQPnJTk2keYXjEgf19i17ZzACBY4Mx"

# Настройки API
API_SETTINGS = {
    "timeout": 30,  # Таймаут запросов в секундах
    "retry_attempts": 3,  # Количество попыток при ошибке
    "retry_delay": 2,  # Задержка между попытками в секундах
}

# Настройки webhook
WEBHOOK_SETTINGS = {
    "enabled": True,  # Включить webhook
    "secret_key": "your_webhook_secret_key",  # Секретный ключ для webhook
    "callback_url": f"{PAYMENT_VERIFICATION_URL}/api/v1/payments/callback",
}

# Настройки валют
SUPPORTED_CURRENCIES = ["USDT", "BTC", "ETH"]

# Минимальные и максимальные суммы
PAYMENT_LIMITS = {
    "USDT": {"min": 1.0, "max": 10000.0},
    "BTC": {"min": 0.0001, "max": 10.0},
    "ETH": {"min": 0.001, "max": 100.0},
}

# Настройки логирования
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "payment_system.log",
}

