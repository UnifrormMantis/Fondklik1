#!/usr/bin/env python3
"""
Тест интеграции с собственной платежной системой
"""

import asyncio
import logging
from custom_payment_api import create_payment, check_payment_status, get_payment_url

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_custom_payment():
    """Тестирование собственной платежной системы"""
    
    print("🧪 Тестирование собственной платежной системы...")
    print("=" * 50)
    
    # Тест 1: Создание платежа
    print("\n1️⃣ Тест создания платежа...")
    try:
        payment_data = await create_payment(
            amount=10.0,
            currency="USDT",
            description="Тестовый платеж",
            user_id=12345
        )
        
        if payment_data:
            print("✅ Платеж создан успешно!")
            print(f"📊 Данные платежа: {payment_data}")
            
            payment_id = payment_data.get('payment_id') or payment_data.get('id')
            if payment_id:
                print(f"🆔 ID платежа: {payment_id}")
                
                # Тест 2: Проверка статуса
                print("\n2️⃣ Тест проверки статуса...")
                status = await check_payment_status(payment_id)
                print(f"📊 Статус платежа: {status}")
                
                # Тест 3: Получение URL для оплаты
                print("\n3️⃣ Тест получения URL для оплаты...")
                payment_url = await get_payment_url(payment_id)
                if payment_url:
                    print(f"🔗 URL для оплаты: {payment_url}")
                else:
                    print("❌ URL для оплаты не получен")
                
            else:
                print("❌ ID платежа не найден в ответе")
        else:
            print("❌ Не удалось создать платеж")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        logger.error(f"Ошибка тестирования: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Тестирование завершено")

async def test_payment_flow():
    """Тест полного потока платежа"""
    
    print("\n🔄 Тест полного потока платежа...")
    print("=" * 50)
    
    try:
        # Создаем платеж
        print("1️⃣ Создание платежа...")
        payment_data = await create_payment(
            amount=25.0,
            currency="USDT", 
            description="Тест полного потока",
            user_id=67890
        )
        
        if not payment_data:
            print("❌ Не удалось создать платеж")
            return
        
        payment_id = payment_data.get('payment_id') or payment_data.get('id')
        print(f"✅ Платеж создан: {payment_id}")
        
        # Проверяем статус несколько раз
        print("\n2️⃣ Мониторинг статуса...")
        for i in range(3):
            status = await check_payment_status(payment_id)
            print(f"   Попытка {i+1}: {status}")
            
            if status == "paid":
                print("✅ Платеж оплачен!")
                break
            elif status == "failed":
                print("❌ Платеж не удался")
                break
            
            await asyncio.sleep(2)  # Ждем 2 секунды между проверками
        
        print("🏁 Мониторинг завершен")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте потока: {e}")
        logger.error(f"Ошибка теста потока: {e}")

def main():
    """Главная функция"""
    print("🤖 Тестирование интеграции с собственной платежной системой")
    print("API Key:", "tO8RcgkEg3ie8CsGWni00d3YHGxjlr5ce6KNykJBbT0"[:20] + "...")
    
    # Запускаем тесты
    asyncio.run(test_custom_payment())
    asyncio.run(test_payment_flow())

if __name__ == "__main__":
    main()











