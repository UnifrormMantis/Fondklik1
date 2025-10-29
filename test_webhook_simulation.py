#!/usr/bin/env python3
"""
Симуляция webhook от платежной системы
"""

import requests
import json
import time

def simulate_payment_webhook():
    """Симулировать webhook о получении платежа"""
    print("🧪 Симуляция webhook от платежной системы")
    print("=" * 50)
    
    # URL webhook сервера
    webhook_url = "http://localhost:8001/"
    
    # Тестовые данные платежа
    test_payment = {
        "user_wallet": "TTestUser1234567890123456789012345",
        "amount": 150.75,
        "transaction_hash": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
        "confirmed_at": "2025-10-06T15:30:00Z",
        "currency": "USDT"
    }
    
    print(f"📡 Отправка webhook на: {webhook_url}")
    print(f"💰 Данные платежа:")
    print(json.dumps(test_payment, indent=2))
    print()
    
    try:
        # Отправляем POST запрос
        response = requests.post(
            webhook_url,
            json=test_payment,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook обработан успешно:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("❌ Ошибка обработки webhook:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к webhook серверу")
        print("💡 Убедитесь, что бот запущен и webhook сервер работает")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_health_check():
    """Проверить статус webhook сервера"""
    print("🏥 Проверка статуса webhook сервера...")
    
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook сервер работает:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"❌ Webhook сервер недоступен: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Webhook сервер не запущен")
        return False
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False

def main():
    """Основная функция"""
    print("🚀 Тестирование системы webhook")
    print("=" * 50)
    
    # Проверяем статус сервера
    if not test_health_check():
        print("\n💡 Для запуска бота с webhook сервером:")
        print("   python3 bot_final.py")
        return
    
    print("\n" + "=" * 50)
    
    # Симулируем несколько платежей
    test_payments = [
        {
            "user_wallet": "TTestUser1234567890123456789012345",
            "amount": 100.0,
            "transaction_hash": "tx_001",
            "confirmed_at": "2025-10-06T15:30:00Z"
        },
        {
            "user_wallet": "TTestUser9876543210987654321098765",
            "amount": 250.5,
            "transaction_hash": "tx_002", 
            "confirmed_at": "2025-10-06T15:31:00Z"
        },
        {
            "user_wallet": "TTestUser5555555555555555555555555",
            "amount": 75.25,
            "transaction_hash": "tx_003",
            "confirmed_at": "2025-10-06T15:32:00Z"
        }
    ]
    
    for i, payment in enumerate(test_payments, 1):
        print(f"\n{i}️⃣ Симуляция платежа {i}:")
        print(f"   Кошелек: {payment['user_wallet']}")
        print(f"   Сумма: {payment['amount']} USDT")
        
        try:
            response = requests.post(
                "http://localhost:8001/",
                json=payment,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Обработан: {result.get('message', 'OK')}")
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        time.sleep(1)  # Пауза между платежами
    
    print("\n" + "=" * 50)
    print("🏁 Тестирование завершено!")

if __name__ == "__main__":
    main()










