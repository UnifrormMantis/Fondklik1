#!/usr/bin/env python3
"""
Скрипт для удаления всех вкладов пользователя
"""

import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_PATH = 'bot_database.db'

def check_user_deposits(user_id):
    """Проверить вклады пользователя"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Проверяем активные вклады
        cursor.execute('''
            SELECT COUNT(*) FROM deposit_payments
            WHERE user_id = ? AND status = 'pending'
        ''', (user_id,))
        active_count = cursor.fetchone()[0]
        
        # Проверяем выплаченные вклады
        cursor.execute('''
            SELECT COUNT(*) FROM deposit_payments
            WHERE user_id = ? AND status = 'paid'
        ''', (user_id,))
        paid_count = cursor.fetchone()[0]
        
        # Проверяем все вклады
        cursor.execute('''
            SELECT COUNT(*) FROM deposit_payments
            WHERE user_id = ?
        ''', (user_id,))
        total_count = cursor.fetchone()[0]
        
        logger.info(f"👤 Пользователь {user_id}:")
        logger.info(f"   🟢 Активных вкладов: {active_count}")
        logger.info(f"   ✅ Выплаченных вкладов: {paid_count}")
        logger.info(f"   📊 Всего вкладов: {total_count}")
        
        return active_count, paid_count, total_count

def delete_user_deposits(user_id):
    """Удалить все вклады пользователя"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Удаляем все вклады пользователя
        cursor.execute('DELETE FROM deposit_payments WHERE user_id = ?', (user_id,))
        deleted_count = cursor.rowcount
        
        # Обновляем счетчики активных депозитов в таблице users
        cursor.execute('''
            UPDATE users 
            SET active_deposits_10 = 0, active_deposits_30 = 0 
            WHERE telegram_id = ?
        ''', (user_id,))
        
        conn.commit()
        
        logger.info(f"🗑️  Удалено {deleted_count} вкладов пользователя {user_id}")
        logger.info(f"🔄 Обновлены счетчики активных депозитов")
        
        return deleted_count

def delete_user_transactions(user_id):
    """Удалить все транзакции пользователя"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Удаляем все транзакции пользователя
        cursor.execute('DELETE FROM user_transactions WHERE user_id = ?', (user_id,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        
        logger.info(f"🗑️  Удалено {deleted_count} транзакций пользователя {user_id}")
        
        return deleted_count

if __name__ == "__main__":
    user_id = 739935417  # Пользователь с ID, заканчивающимся на 5417
    
    logger.info(f"🔍 Проверяем вклады пользователя {user_id}")
    active_count, paid_count, total_count = check_user_deposits(user_id)
    
    if total_count > 0:
        logger.info(f"\n🗑️  Удаляем все вклады пользователя {user_id}")
        deleted_deposits = delete_user_deposits(user_id)
        
        logger.info(f"\n🗑️  Удаляем все транзакции пользователя {user_id}")
        deleted_transactions = delete_user_transactions(user_id)
        
        logger.info(f"\n✅ ГОТОВО!")
        logger.info(f"👤 Пользователь: {user_id}")
        logger.info(f"🗑️  Удалено вкладов: {deleted_deposits}")
        logger.info(f"🗑️  Удалено транзакций: {deleted_transactions}")
        
        # Проверяем результат
        logger.info(f"\n🔍 Проверяем результат...")
        check_user_deposits(user_id)
    else:
        logger.info(f"ℹ️  У пользователя {user_id} нет вкладов для удаления")
