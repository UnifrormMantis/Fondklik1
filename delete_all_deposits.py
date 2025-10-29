#!/usr/bin/env python3
"""
Скрипт для удаления всех вкладов у всех пользователей
"""

import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_PATH = 'bot_database.db'

def delete_all_deposits():
    """Удалить все вклады у всех пользователей"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Удаляем все вклады
        cursor.execute('DELETE FROM deposit_payments')
        deleted_deposits = cursor.rowcount
        
        # Удаляем все транзакции
        cursor.execute('DELETE FROM user_transactions')
        deleted_transactions = cursor.rowcount
        
        # Обновляем счетчики активных депозитов у всех пользователей
        cursor.execute('UPDATE users SET active_deposits_10 = 0, active_deposits_30 = 0')
        updated_users = cursor.rowcount
        
        conn.commit()
        
        logger.info(f"🗑️  Удалено {deleted_deposits} вкладов")
        logger.info(f"🗑️  Удалено {deleted_transactions} транзакций")
        logger.info(f"🔄 Обновлены счетчики у {updated_users} пользователей")

def check_result():
    """Проверяем результат"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Проверяем количество вкладов
        cursor.execute('SELECT COUNT(*) FROM deposit_payments')
        deposits_count = cursor.fetchone()[0]
        
        # Проверяем количество транзакций
        cursor.execute('SELECT COUNT(*) FROM user_transactions')
        transactions_count = cursor.fetchone()[0]
        
        # Проверяем пользователей с активными депозитами
        cursor.execute('''
            SELECT user_id, COUNT(*) as deposit_count
            FROM deposit_payments
            WHERE status = 'pending'
            GROUP BY user_id
        ''')
        users_with_deposits = cursor.fetchall()
        
        logger.info(f"📊 Результат:")
        logger.info(f"   Вкладов в базе: {deposits_count}")
        logger.info(f"   Транзакций в базе: {transactions_count}")
        logger.info(f"   Пользователей с активными депозитами: {len(users_with_deposits)}")
        
        if len(users_with_deposits) == 0:
            logger.info("✅ Все вклады успешно удалены!")
        else:
            logger.warning("⚠️ Остались пользователи с активными депозитами:")
            for user_id, count in users_with_deposits:
                logger.warning(f"   👤 Пользователь {user_id}: {count} депозитов")

if __name__ == "__main__":
    logger.info("🗑️  Удаляем все вклады у всех пользователей")
    
    # Удаляем все вклады
    delete_all_deposits()
    
    # Проверяем результат
    logger.info("\n🔍 Проверяем результат...")
    check_result()
    
    logger.info("\n✅ ГОТОВО! Теперь все пользователи могут создавать новые депозиты")















