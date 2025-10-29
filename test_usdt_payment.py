#!/usr/bin/env python3
"""
Тест интеграции с USDT платежной системой
"""

import asyncio
import logging
from payment_verification_client import PaymentVerificationClient
from payment_config import USDT_PAYMENT_API_KEY, PAYMENT_VERIFICATION_URL, PAYMENT_WALLET

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_usdt_payment_system():
    """Тестирование системы USDT платежей"""
    
    print("🧪 Тестирование системы USDT платежей...")
    print("=" * 50)
    
    # Инициализация клиента
    client = PaymentVerificationClient(
        api_key=USDT_PAYMENT_API_KEY,
        base_url=PAYMENT_VERIFICATION_URL
    )
    
    # Тест 1: Получение информации о кошельке
    print("\n1️⃣ Получение информации о кошельке...")
    try:
        wallet_info = client.get_wallet_info()
        
        if wallet_info.get("success"):
            print("✅ Информация о кошельке получена:")
            print(f"   🏦 Адрес: {wallet_info['wallet_address']}")
            print(f"   💰 Баланс: {wallet_info['balance']} {wallet_info['currency']}")
        else:
            print(f"❌ Ошибка получения информации: {wallet_info.get('error')}")
    except Exception as e:
        print(f"❌ Исключение при получении информации: {e}")
    
    # Тест 2: Проверка тестового платежа
    print("\n2️⃣ Проверка тестового платежа...")
    try:
        test_result = client.verify_payment(
            user_wallet="TTestWallet1234567890123456789012345",
            expected_amount=1.00,
            currency="USDT",
            description="Тестовый платеж"
        )
        
        if test_result.get("success"):
            if test_result.get("payment_found"):
                print(f"✅ Платеж найден: {test_result['received_amount']} USDT")
                print(f"   🔗 Транзакция: {test_result.get('transaction_hash', 'N/A')}")
            else:
                print(f"ℹ️  Платеж не найден (это нормально для тестового кошелька)")
                print(f"   📝 Сообщение: {test_result.get('message', 'N/A')}")
        else:
            print(f"❌ Ошибка проверки: {test_result.get('error')}")
    except Exception as e:
        print(f"❌ Исключение при проверке платежа: {e}")
    
    # Тест 3: Проверка с реальным кошельком (если указан)
    if PAYMENT_WALLET and PAYMENT_WALLET != "TWJ5wQPnJTk2keYXjEgf19i17ZzACBY4Mx":
        print(f"\n3️⃣ Проверка с кошельком {PAYMENT_WALLET}...")
        try:
            real_result = client.verify_payment(
                user_wallet=PAYMENT_WALLET,
                expected_amount=0.01,
                currency="USDT",
                description="Тест с реальным кошельком"
            )
            
            if real_result.get("success"):
                if real_result.get("payment_found"):
                    print(f"✅ Платеж найден: {real_result['received_amount']} USDT")
                else:
                    print(f"ℹ️  Платеж не найден")
            else:
                print(f"❌ Ошибка: {real_result.get('error')}")
        except Exception as e:
            print(f"❌ Исключение: {e}")
    
    # Тест 4: Ожидание платежа (краткий тест)
    print("\n4️⃣ Тест ожидания платежа (5 секунд)...")
    try:
        wait_result = client.wait_for_payment(
            user_wallet="TTestWallet1234567890123456789012345",
            expected_amount=1.00,
            timeout=5,  # 5 секунд
            check_interval=2  # проверка каждые 2 секунды
        )
        
        if wait_result.get("success"):
            if wait_result.get("payment_found"):
                print(f"✅ Платеж найден при ожидании: {wait_result['received_amount']} USDT")
            else:
                print(f"ℹ️  Платеж не найден за время ожидания (это нормально)")
        else:
            print(f"❌ Ошибка ожидания: {wait_result.get('error')}")
    except Exception as e:
        print(f"❌ Исключение при ожидании: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Тестирование завершено!")
    
    # Вывод конфигурации
    print(f"\n📋 Конфигурация:")
    print(f"   🔑 API Key: {USDT_PAYMENT_API_KEY[:20]}...")
    print(f"   🌐 URL: {PAYMENT_VERIFICATION_URL}")
    print(f"   🏦 Кошелек: {PAYMENT_WALLET}")

def main():
    """Главная функция"""
    print("🤖 Тестирование интеграции с USDT платежной системой")
    print(f"🔑 API Key: {USDT_PAYMENT_API_KEY[:20]}...")
    print(f"🌐 URL: {PAYMENT_VERIFICATION_URL}")
    
    # Запускаем тесты
    asyncio.run(test_usdt_payment_system())

if __name__ == "__main__":
    main()










