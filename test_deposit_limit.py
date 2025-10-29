#!/usr/bin/env python3
"""
Тест ограничения количества активных вкладов
"""

import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_PATH = 'bot_database.db'

def get_user_active_deposits_count(user_id):
    """Получить количество активных депозитов пользователя"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM deposit_payments
            WHERE user_id = ? AND status = 'pending'
        ''', (user_id,))
        return cursor.fetchone()[0]

def test_deposit_limit():
    """Тестируем ограничение депозитов"""
    
    # Тестируем с админом (у него 30 депозитов)
    admin_id = 739935417
    admin_count = get_user_active_deposits_count(admin_id)
    logger.info(f"👤 Админ {admin_id}: {admin_count} активных депозитов")
    
    if admin_count >= 10:
        logger.info("✅ Ограничение сработает - админ не сможет создать новый депозит")
    else:
        logger.info("❌ Ограничение не сработает - админ может создать новый депозит")
    
    # Тестируем с обычным пользователем (если есть)
    test_user_id = 123456789  # Несуществующий пользователь
    test_count = get_user_active_deposits_count(test_user_id)
    logger.info(f"👤 Тестовый пользователь {test_user_id}: {test_count} активных депозитов")
    
    if test_count >= 10:
        logger.info("✅ Ограничение сработает - пользователь не сможет создать новый депозит")
    else:
        logger.info("❌ Ограничение не сработает - пользователь может создать новый депозит")
    
    # Показываем всех пользователей с активными депозитами
    logger.info("\n📊 Все пользователи с активными депозитами:")
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, COUNT(*) as deposit_count
            FROM deposit_payments
            WHERE status = 'pending'
            GROUP BY user_id
            ORDER BY deposit_count DESC
        ''')
        
        users = cursor.fetchall()
        for user_id, count in users:
            logger.info(f"   👤 Пользователь {user_id}: {count} активных депозитов")
            if count >= 10:
                logger.info(f"      ⚠️  Достигнут лимит в 10 депозитов!")

if __name__ == "__main__":
    logger.info("🧪 Тестируем ограничение количества активных вкладов")
    test_deposit_limit()















