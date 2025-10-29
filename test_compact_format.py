#!/usr/bin/env python3
"""
Тест компактного формата для кнопки "Ваши вклады"
"""

import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_PATH = 'bot_database.db'

def test_compact_message(user_id):
    """Тестируем компактное сообщение"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Получаем активные депозиты
            cursor.execute('''
                SELECT dp.original_amount, dp.deposit_type, dp.days_remaining, dp.created_at
                FROM deposit_payments dp
                WHERE dp.user_id = ? AND dp.status = 'pending'
                ORDER BY dp.created_at DESC
            ''', (user_id,))
            active_deposits = cursor.fetchall()
            
            # Получаем выплаченные депозиты
            cursor.execute('''
                SELECT dp.original_amount, dp.deposit_type, dp.payment_date, dp.return_amount
                FROM deposit_payments dp
                WHERE dp.user_id = ? AND dp.status = 'paid'
                ORDER BY dp.payment_date DESC
            ''', (user_id,))
            paid_deposits = cursor.fetchall()
        
        # Строим компактное сообщение
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
                type_text = "30д (30%)" if deposit_type == "30_days" else "10д (8%)"
                
                # Компактный формат
                message_text += f"{i}. 💰{amount} USDT {type_text} 📅{date_str} ⏰{days_remaining}д\n"
            
            # Если депозитов больше 10, показываем общую информацию
            if len(active_deposits) > 10:
                total_amount = sum(deposit[0] for deposit in active_deposits)
                message_text += f"\n... и еще {len(active_deposits) - 10} депозитов\n"
                message_text += f"💰 Общая сумма: {total_amount} USDT\n"
        else:
            message_text += "🟢 АКТИВНЫЕ ВКЛАДЫ:\nНет активных вкладов\n\n"
        
        # Показываем историю выплаченных вкладов
        if paid_deposits:
            message_text += "\n📜 ИСТОРИЯ ВЫПЛАЧЕННЫХ ВКЛАДОВ:\n"
            for i, deposit in enumerate(paid_deposits[:5], 1):
                amount, deposit_type, payment_date, return_amount = deposit
                
                # Определяем тип депозита
                type_text = "30д (30%)" if deposit_type == "30_days" else "10д (8%)"
                
                # Компактный формат
                message_text += f"{i}. 💰{amount}→{return_amount} USDT {type_text} 📅{payment_date}\n"
            
            # Если выплаченных депозитов больше 5, показываем общую информацию
            if len(paid_deposits) > 5:
                message_text += f"... и еще {len(paid_deposits) - 5} выплаченных депозитов\n"
        else:
            message_text += "\n📜 ИСТОРИЯ ВЫПЛАЧЕННЫХ ВКЛАДОВ:\nНет выплаченных депозитов\n"
        
        logger.info(f"✅ Компактное сообщение построено. Длина: {len(message_text)} символов")
        logger.info(f"📝 Сообщение:\n{message_text}")
        
        return message_text
        
    except Exception as e:
        logger.error(f"❌ Ошибка при построении компактного сообщения: {e}")
        return None

if __name__ == "__main__":
    admin_id = 739935417  # Правильный ID админа
    
    logger.info(f"🧪 Тестируем компактный формат для админа {admin_id}")
    
    # Тестируем компактное сообщение
    message = test_compact_message(admin_id)
    
    if message:
        logger.info("✅ Тест компактного формата прошел успешно!")
    else:
        logger.error("❌ Тест компактного формата не прошел!")















