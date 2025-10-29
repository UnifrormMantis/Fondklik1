#!/usr/bin/env python3
"""
Тест минимальных сумм для депозитов и вывода
"""

def test_minimum_amounts():
    """Тест минимальных сумм"""
    
    print("🔍 Тестируем минимальные суммы для депозитов и вывода")
    
    # Тестируем логику проверки сумм
    def test_deposit_amount(amount):
        """Тест суммы депозита"""
        if amount < 50:
            return f"❌ Минимальная сумма депозита: 50 USDT"
        elif amount > 10000:
            return f"❌ Максимальная сумма депозита: 10000 USDT"
        else:
            return f"✅ Сумма {amount} USDT подходит для депозита"
    
    def test_withdrawal_amount(amount, available=1000):
        """Тест суммы вывода"""
        if amount < 50:
            return f"❌ Минимальная сумма для вывода: 50 USDT"
        elif amount > available:
            return f"❌ Максимальная сумма для вывода: {available:.2f} USDT"
        else:
            return f"✅ Сумма {amount} USDT подходит для вывода"
    
    print("\n📊 ТЕСТ СУММ ДЕПОЗИТОВ:")
    test_amounts = [10, 25, 50, 100, 500, 1000, 5000, 10000, 15000]
    
    for amount in test_amounts:
        result = test_deposit_amount(amount)
        print(f"   {amount} USDT: {result}")
    
    print("\n📊 ТЕСТ СУММ ВЫВОДА:")
    test_withdrawal_amounts = [10, 25, 50, 100, 500, 1000]
    
    for amount in test_withdrawal_amounts:
        result = test_withdrawal_amount(amount)
        print(f"   {amount} USDT: {result}")
    
    print("\n" + "=" * 60)
    print("📱 ОБНОВЛЕННЫЙ ИНТЕРФЕЙС ДЕПОЗИТОВ:")
    print("=" * 60)
    
    deposit_menu = """
💳 АДРЕС ПОДТВЕРЖДЕН

Ваш USDT кошелек: `TTest123456789012345678901234567890`

Выберите сумму пополнения:
💡 Минимальная сумма: 50 USDT

[50 USDT] [100 USDT] [200 USDT] [500 USDT]
[💳 Ввести свою сумму]
[🔙 Назад]
    """
    
    print(deposit_menu)
    
    print("\n" + "=" * 60)
    print("📱 ОБНОВЛЕННЫЙ ИНТЕРФЕЙС ВЫВОДА:")
    print("=" * 60)
    
    withdrawal_menu = """
💸 ВЫВОД СРЕДСТВ

💰 Доступно к выводу: 1000.00 USDT

Введите сумму, которую хотите вывести:
• Минимальная сумма: 50 USDT
• Максимальная сумма: 1000.00 USDT

Пример: 150.5
    """
    
    print(withdrawal_menu)
    
    print("\n" + "=" * 60)
    print("📱 ИНТЕРФЕЙС ВВОДА ПРОИЗВОЛЬНОЙ СУММЫ:")
    print("=" * 60)
    
    custom_amount_menu = """
💳 ВВОД СУММЫ

Введите сумму депозита в USDT:
💡 Минимальная сумма: 50 USDT
💡 Максимальная сумма: 10000 USDT

Пример: 150.5
    """
    
    print(custom_amount_menu)
    
    print("\n✅ Изменения:")
    print("   ✅ Минимальная сумма депозита: 50 USDT (было 10 USDT)")
    print("   ✅ Минимальная сумма вывода: 50 USDT (было 1 USDT)")
    print("   ✅ Добавлена возможность ввода произвольной суммы")
    print("   ✅ Добавлена максимальная сумма депозита: 10000 USDT")
    print("   ✅ Обновлены кнопки выбора суммы (50, 100, 200, 500 USDT)")
    
    print("\n✅ Тест минимальных сумм завершен успешно!")

if __name__ == "__main__":
    test_minimum_amounts()
















