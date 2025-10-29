#!/usr/bin/env python3
"""
Тест для проверки работы кнопки "Ваши вклады"
"""

import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_PATH = 'bot_database.db'

def test_get_user_active_deposits(user_id):
    """Тестируем получение активных депозитов"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT dp.original_amount, dp.deposit_type, dp.days_remaining, dp.created_at
                FROM deposit_payments dp
                WHERE dp.user_id = ? AND dp.status = 'pending'
                ORDER BY dp.created_at DESC
            ''', (user_id,))
            deposits = cursor.fetchall()
            logger.info(f"✅ Активных депозитов найдено: {len(deposits)}")
            return deposits
    except Exception as e:
        logger.error(f"❌ Ошибка при получении активных депозитов: {e}")
        return None

def test_get_user_paid_deposits(user_id):
    """Тестируем получение выплаченных депозитов"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT dp.original_amount, dp.deposit_type, dp.payment_date, dp.return_amount
                FROM deposit_payments dp
                WHERE dp.user_id = ? AND dp.status = 'paid'
                ORDER BY dp.payment_date DESC
            ''', (user_id,))
            deposits = cursor.fetchall()
            logger.info(f"✅ Выплаченных депозитов найдено: {len(deposits)}")
            return deposits
    except Exception as e:
        logger.error(f"❌ Ошибка при получении выплаченных депозитов: {e}")
        return None

def test_message_construction(user_id):
    """Тестируем построение сообщения"""
    try:
        logger.info(f"🔍 Тестируем построение сообщения для пользователя {user_id}")
        
        # Получаем данные
        active_deposits = test_get_user_active_deposits(user_id)
        paid_deposits = test_get_user_paid_deposits(user_id)
        
        # Строим сообщение
        message_text = "📊 ВАШИ ВКЛАДЫ\n\n"
        
        # Показываем активные вклады (ограничиваем до 10)
        if active_deposits:
            message_text += "🟢 АКТИВНЫЕ ВКЛАДЫ:\n"
            # Показываем только первые 10 депозитов
            for i, deposit in enumerate(active_deposits[:10], 1):
                amount, deposit_type, days_remaining, created_at = deposit
                
                # Форматируем дату
                date_str = created_at.split(' ')[0] if created_at else "Неизвестно"
                
                # Определяем тип депозита
                type_text = "30 дней (30%)" if deposit_type == "30_days" else "10 дней (8%)"
                
                message_text += f"""
{i}. 💰 {amount} USDT
   📅 Тип: {type_text}
   📆 Дата создания: {date_str}
   ⏰ Дней до выплаты: {days_remaining}
   🟢 Статус: Активен
                """
            
            # Если депозитов больше 10, показываем общую информацию
            if len(active_deposits) > 10:
                total_amount = sum(deposit[0] for deposit in active_deposits)
                message_text += f"\n... и еще {len(active_deposits) - 10} депозитов\n"
                message_text += f"💰 Общая сумма активных вкладов: {total_amount} USDT\n"
        else:
            message_text += "🟢 АКТИВНЫЕ ВКЛАДЫ:\nНет активных вкладов\n\n"
        
        # Показываем историю выплаченных вкладов
        if paid_deposits:
            message_text += "\n📜 ИСТОРИЯ ВЫПЛАЧЕННЫХ ВКЛАДОВ:\n"
            for i, deposit in enumerate(paid_deposits, 1):
                amount, deposit_type, payment_date, return_amount = deposit
                
                # Определяем тип депозита
                type_text = "30 дней (30%)" if deposit_type == "30_days" else "10 дней (8%)"
                
                message_text += f"""
{i}. 💰 {amount} USDT → {return_amount} USDT
   📅 Тип: {type_text}
   📆 Дата выплаты: {payment_date}
   ✅ Статус: Выплачен
                """
        else:
            message_text += "\n📜 ИСТОРИЯ ВЫПЛАЧЕННЫХ ВКЛАДОВ:\nНет выплаченных депозитов\n"
        
        logger.info(f"✅ Сообщение построено успешно. Длина: {len(message_text)} символов")
        logger.info(f"📝 Первые 500 символов сообщения:\n{message_text[:500]}...")
        
        return message_text
        
    except Exception as e:
        logger.error(f"❌ Ошибка при построении сообщения: {e}")
        return None

if __name__ == "__main__":
    admin_id = 739935417  # Правильный ID админа
    
    logger.info(f"🧪 Тестируем кнопку 'Ваши вклады' для админа {admin_id}")
    
    # Тестируем построение сообщения
    message = test_message_construction(admin_id)
    
    if message:
        logger.info("✅ Тест прошел успешно!")
    else:
        logger.error("❌ Тест не прошел!")















