#!/usr/bin/env python3
"""
Отладка процесса создания депозита
"""

import sqlite3
import logging
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_PATH = 'bot_database.db'

def check_user_deposits(user_id):
    """Проверяем депозиты пользователя"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Проверяем активные депозиты
        cursor.execute('''
            SELECT COUNT(*) FROM deposit_payments
            WHERE user_id = ? AND status = 'pending'
        ''', (user_id,))
        active_count = cursor.fetchone()[0]
        
        # Проверяем все депозиты
        cursor.execute('''
            SELECT COUNT(*) FROM deposit_payments
            WHERE user_id = ?
        ''', (user_id,))
        total_count = cursor.fetchone()[0]
        
        logger.info(f"👤 Пользователь {user_id}:")
        logger.info(f"   🟢 Активных депозитов: {active_count}")
        logger.info(f"   📊 Всего депозитов: {total_count}")
        
        if active_count >= 10:
            logger.warning(f"   ⚠️ ЛИМИТ ДОСТИГНУТ! Нельзя создавать новые депозиты")
        else:
            logger.info(f"   ✅ Можно создать еще {10 - active_count} депозитов")
        
        return active_count

def test_deposit_validation(user_id, amount):
    """Тестируем валидацию депозита"""
    logger.info(f"🧪 Тестируем валидацию депозита для пользователя {user_id} на сумму {amount}")
    
    # Проверяем минимальную сумму
    if amount < 50:
        logger.error(f"❌ Минимальная сумма депозита: 50 USDT")
        return False
    
    # Проверяем количество активных вкладов
    active_deposits_count = check_user_deposits(user_id)
    if active_deposits_count >= 10:
        logger.error(f"❌ У пользователя уже есть {active_deposits_count} активных вкладов")
        logger.error("❌ Максимальное количество активных вкладов: 10")
        logger.error("❌ Дождитесь выплаты одного из вкладов, чтобы создать новый.")
        return False
    
    logger.info("✅ Валидация прошла успешно!")
    return True

def main():
    logger.info("🔍 Отладка процесса создания депозита")
    
    # Тестируем с разными пользователями
    test_users = [798427688, 123456789, 555666777, 111222333, 987654321]
    test_amount = 100.0
    
    for user_id in test_users:
        logger.info(f"\n{'='*50}")
        logger.info(f"Тестируем пользователя {user_id}")
        logger.info(f"{'='*50}")
        
        result = test_deposit_validation(user_id, test_amount)
        
        if result:
            logger.info(f"✅ Пользователь {user_id} может создать депозит")
        else:
            logger.info(f"❌ Пользователь {user_id} НЕ может создать депозит")

if __name__ == "__main__":
    main()















