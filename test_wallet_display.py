#!/usr/bin/env python3
"""
Тест отображения адресов кошельков в выплатах вкладов
"""

import sqlite3
import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_final import FastBot

def test_wallet_display():
    """Тест отображения адресов кошельков"""
    
    print("🔍 Тестируем отображение адресов кошельков в выплатах вкладов")
    
    # Создаем экземпляр бота
    bot = FastBot()
    
    # Проверяем админские права
    admin_id = 739935417
    is_admin = bot.is_admin(admin_id)
    print(f"👤 Является админом: {is_admin}")
    
    if not is_admin:
        print("❌ Пользователь не является админом")
        return
    
    # Получаем данные о выплатах
    print("📊 Получаем данные о выплатах...")
    try:
        payments_by_day = bot.get_deposit_payments_by_day()
        print(f"✅ Получено {len(payments_by_day)} групп выплат")
        
        if not payments_by_day:
            print("❌ Нет данных о выплатах")
            return
        
        # Показываем результат
        print("\n📋 РЕЗУЛЬТАТ:")
        print("💰 ВЫПЛАТЫ ВКЛАДОВ")
        print()
        print("📅 Расписание по дням:")
        print()
        
        for day_data in payments_by_day:
            days_remaining, payment_date, payment_count, total_amount, payment_details = day_data
            
            if days_remaining == 1:
                # Последний день - показываем все детали
                print(f"🚨 ДЕНЬ {days_remaining} - {payment_date} (СЕГОДНЯ!)")
                print(f"📊 Количество выплат: {payment_count}")
                print(f"💰 Общая сумма: {total_amount:.2f} USDT")
                print()
                print("👥 ДЕТАЛИ ВЫПЛАТ:")
                print(payment_details)
                print()
            else:
                # Обычные дни
                print(f"📅 ДЕНЬ {days_remaining} - {payment_date}")
                print(f"📊 Количество выплат: {payment_count}")
                print(f"💰 Общая сумма: {total_amount:.2f} USDT")
                print()
        
        print("✅ Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_wallet_display()
