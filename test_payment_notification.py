#!/usr/bin/env python3
"""
Тест системы уведомления платежной системы о ожидаемых платежах
"""

import asyncio
from payment_verification_client import PaymentVerificationClient
from payment_config import USDT_PAYMENT_API_KEY, PAYMENT_VERIFICATION_URL

async def test_payment_notification():
    """Тест уведомления платежной системы"""
    print("🧪 Тестирование системы уведомления платежей")
    print("=" * 50)
    
    # Инициализация клиента
    client = PaymentVerificationClient(
        api_key=USDT_PAYMENT_API_KEY,
        base_url=PAYMENT_VERIFICATION_URL
    )
    
    # Тестовые данные
    test_user_wallet = "TTestUser1234567890123456789012345"
    test_description = "Тестовый вклад 30 дней от пользователя 123456789"
    
    print(f"🔑 API Key: {USDT_PAYMENT_API_KEY[:20]}...")
    print(f"🌐 URL: {PAYMENT_VERIFICATION_URL}")
    print(f"👤 Тестовый кошелек: {test_user_wallet}")
    print()
    
    # 1. Получаем информацию о кошельке для приема платежей
    print("1️⃣ Получение информации о кошельке для приема платежей...")
    wallet_info = client.get_wallet_info()
    
    if wallet_info.get("success"):
        print(f"✅ Кошелек для приема: {wallet_info['wallet_address']}")
        print(f"💰 Баланс: {wallet_info.get('balance', 0)} USDT")
    else:
        print(f"❌ Ошибка: {wallet_info.get('error', 'Неизвестная ошибка')}")
        return
    
    print()
    
    # 2. Уведомляем платежную систему о ожидаемом платеже
    print("2️⃣ Уведомление платежной системы о ожидаемом платеже...")
    notification_result = client.notify_expected_payment(
        user_wallet=test_user_wallet,
        currency="USDT",
        description=test_description
    )
    
    if notification_result.get("success"):
        print("✅ Платежная система уведомлена")
        print(f"📝 Сообщение: {notification_result.get('message', 'N/A')}")
    else:
        print(f"❌ Ошибка уведомления: {notification_result.get('error', 'Неизвестная ошибка')}")
        # Продолжаем тест, так как это может быть не реализовано в API
    
    print()
    
    # 3. Проверяем платеж (симуляция)
    print("3️⃣ Проверка платежа (симуляция)...")
    payment_result = client.verify_payment(
        user_wallet=test_user_wallet,
        expected_amount=50.0,
        currency="USDT",
        description=test_description
    )
    
    if payment_result.get("success"):
        if payment_result.get("payment_found"):
            print(f"✅ Платеж найден: {payment_result['received_amount']} USDT")
            print(f"🔗 Транзакция: {payment_result.get('transaction_hash', 'N/A')}")
        else:
            print("ℹ️  Платеж не найден (это нормально для тестового кошелька)")
            print(f"📝 Сообщение: {payment_result.get('message', 'N/A')}")
    else:
        print(f"❌ Ошибка проверки: {payment_result.get('error', 'Неизвестная ошибка')}")
    
    print()
    print("=" * 50)
    print("🏁 Тестирование завершено!")
    print()
    print("📋 Логика работы:")
    print("1. Пользователь вводит свой кошелек")
    print("2. Бот получает кошелек для приема платежей")
    print("3. Бот уведомляет платежную систему о ожидаемом платеже")
    print("4. Пользователь отправляет USDT на кошелек для приема")
    print("5. Бот проверяет поступления от кошелька пользователя")
    print("6. Платежная система сообщает полученную сумму")
    print("7. Бот создает вклад на полученную сумму")

if __name__ == "__main__":
    asyncio.run(test_payment_notification())










