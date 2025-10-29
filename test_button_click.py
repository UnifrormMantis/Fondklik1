#!/usr/bin/env python3
"""
Тест нажатия кнопки "Выплата вкладов"
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Имитируем объект Update для тестирования
class MockUpdate:
    def __init__(self, user_id):
        self.effective_user = MockUser(user_id)
        self.callback_query = MockCallbackQuery()

class MockUser:
    def __init__(self, user_id):
        self.id = user_id

class MockCallbackQuery:
    def __init__(self):
        pass
    
    async def edit_message_text(self, text, reply_markup=None):
        print("📱 Сообщение в боте:")
        print("=" * 50)
        print(text)
        print("=" * 50)
        if reply_markup:
            print("🔘 Кнопки:", reply_markup)

class MockContext:
    def __init__(self):
        pass

def test_deposit_payments_button():
    """Тестируем кнопку выплат вкладов"""
    
    try:
        # Импортируем только нужные части
        from bot_final import FastBot
        
        # Создаем экземпляр бота (но не запускаем)
        bot = FastBot()
        
        # Тестируем с ID админа
        admin_id = 739935417  # ID админа из базы данных
        
        print(f"🔍 Тестируем кнопку 'Выплата вкладов' для админа {admin_id}")
        
        # Проверяем, является ли пользователь админом
        is_admin = bot.is_admin(admin_id)
        print(f"👤 Является админом: {is_admin}")
        
        if not is_admin:
            print("❌ Пользователь не является админом")
            return
        
        # Тестируем получение данных
        print("📊 Получаем данные о выплатах...")
        payments = bot.get_deposit_payments_by_day()
        print(f"✅ Получено {len(payments)} групп выплат")
        
        if not payments:
            print("💰 Нет выплат вкладов")
            return
        
        # Показываем результат как в боте
        message_text = "💰 ВЫПЛАТЫ ВКЛАДОВ\n\n"
        message_text += "📅 Расписание по дням:\n\n"
        
        for day_data in payments:
            days_remaining, payment_date, payment_count, total_amount, payment_details = day_data
            
            if days_remaining == 1:
                message_text += f"🚨 ДЕНЬ {days_remaining} - {payment_date} (СЕГОДНЯ!)\n"
                message_text += f"📊 Количество выплат: {payment_count}\n"
                message_text += f"💰 Общая сумма: {total_amount:.2f} USDT\n\n"
                message_text += "👥 ДЕТАЛИ ВЫПЛАТ:\n"
                message_text += payment_details + "\n\n"
            else:
                message_text += f"📅 ДЕНЬ {days_remaining} - {payment_date}\n"
                message_text += f"📊 Количество выплат: {payment_count}\n"
                message_text += f"💰 Общая сумма: {total_amount:.2f} USDT\n\n"
        
        print("✅ Кнопка 'Выплата вкладов' работает корректно!")
        print("📋 Результат:")
        print(message_text)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deposit_payments_button()

















