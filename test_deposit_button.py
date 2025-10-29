#!/usr/bin/env python3
"""
Тестирование кнопки "Выплата вкладов"
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_final import FastBot

def test_deposit_payments_button():
    """Тестируем кнопку выплат вкладов"""
    
    try:
        # Создаем экземпляр бота
        bot = FastBot()
        
        # Тестируем метод get_deposit_payments_by_day
        print("🔍 Тестируем метод get_deposit_payments_by_day...")
        payments = bot.get_deposit_payments_by_day()
        
        if not payments:
            print("❌ Нет данных о выплатах")
            return
        
        print(f"✅ Получено {len(payments)} групп выплат")
        
        # Показываем результат как в боте
        message_text = "💰 ВЫПЛАТЫ ВКЛАДОВ\n\n"
        message_text += "📅 Расписание по дням:\n\n"
        
        for day_data in payments:
            days_remaining, payment_date, payment_count, total_amount, payment_details = day_data
            
            if days_remaining == 1:
                # Последний день - показываем все детали
                message_text += f"🚨 ДЕНЬ {days_remaining} - {payment_date} (СЕГОДНЯ!)\n"
                message_text += f"📊 Количество выплат: {payment_count}\n"
                message_text += f"💰 Общая сумма: {total_amount:.2f} USDT\n\n"
                message_text += "👥 ДЕТАЛИ ВЫПЛАТ:\n"
                message_text += payment_details + "\n\n"
            else:
                # Обычные дни
                message_text += f"📅 ДЕНЬ {days_remaining} - {payment_date}\n"
                message_text += f"📊 Количество выплат: {payment_count}\n"
                message_text += f"💰 Общая сумма: {total_amount:.2f} USDT\n\n"
        
        print("📋 Результат (как будет показано в боте):")
        print("=" * 50)
        print(message_text)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deposit_payments_button()

















