#!/usr/bin/env python3
"""
Утилиты для работы с оптимизированной базой данных
Интегрируется в основной бот для автоматического обновления статистики
"""

import sqlite3
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер для работы с оптимизированной базой данных"""
    
    def __init__(self, db_path='bot_database.db'):
        self.db_path = db_path
    
    def update_user_stats(self, user_id=None):
        """
        Обновляет статистику пользователя
        
        Args:
            user_id (int, optional): ID пользователя. Если None - обновляет всех
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            where_clause = f"WHERE telegram_id = {user_id}" if user_id else ""
            
            # Обновляем все статистики
            cursor.execute(f"""
                UPDATE users SET 
                    total_deposits = (
                        SELECT COALESCE(SUM(amount), 0) 
                        FROM deposits 
                        WHERE deposits.user_id = users.telegram_id
                    ),
                    total_withdrawals = (
                        SELECT COALESCE(SUM(amount), 0) 
                        FROM referral_withdrawals 
                        WHERE referral_withdrawals.user_id = users.telegram_id 
                        AND status = 'completed'
                    ),
                    total_earned = (
                        SELECT COALESCE(SUM(amount), 0) 
                        FROM referral_payments 
                        WHERE referral_payments.referrer_id = users.telegram_id
                    ),
                    active_deposits_10 = (
                        SELECT COUNT(*) 
                        FROM deposits 
                        WHERE deposits.user_id = users.telegram_id 
                        AND status = 'active' 
                        AND deposit_type = '10_days'
                    ),
                    active_deposits_30 = (
                        SELECT COUNT(*) 
                        FROM deposits 
                        WHERE deposits.user_id = users.telegram_id 
                        AND status = 'active' 
                        AND deposit_type = '30_days'
                    ),
                    last_activity = CURRENT_TIMESTAMP
                {where_clause}
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Статистика обновлена для {'пользователя' if user_id else 'всех пользователей'}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
            return False
    
    def get_user_info(self, telegram_id):
        """
        Получает полную информацию о пользователе из одной таблицы
        
        Args:
            telegram_id (int): ID пользователя в Telegram
            
        Returns:
            dict: Полная информация о пользователе или None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    telegram_id, username, first_name, last_name,
                    wallet_address, balance, total_deposits, total_earned, 
                    total_withdrawals, active_deposits_10, active_deposits_30,
                    referral_code, referred_by, referrer_id, is_admin,
                    created_at, last_activity
                FROM users 
                WHERE telegram_id = ?
            """, (telegram_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'telegram_id': result[0],
                    'username': result[1],
                    'first_name': result[2],
                    'last_name': result[3],
                    'wallet_address': result[4],
                    'balance': result[5],
                    'total_deposits': result[6],
                    'total_earned': result[7],
                    'total_withdrawals': result[8],
                    'active_deposits_10': result[9],
                    'active_deposits_30': result[10],
                    'referral_code': result[11],
                    'referred_by': result[12],
                    'referrer_id': result[13],
                    'is_admin': bool(result[14]),
                    'created_at': result[15],
                    'last_activity': result[16],
                    'available_balance': result[7] - result[8]  # total_earned - total_withdrawals
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе: {e}")
            return None
    
    def save_wallet_address(self, telegram_id, wallet_address):
        """
        Сохраняет адрес кошелька пользователя
        
        Args:
            telegram_id (int): ID пользователя
            wallet_address (str): Адрес кошелька
            
        Returns:
            bool: True если успешно сохранено
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET wallet_address = ?, last_activity = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            """, (wallet_address, telegram_id))
            
            conn.commit()
            conn.close()
            
            # Обновляем статистику пользователя
            self.update_user_stats(telegram_id)
            
            logger.info(f"Кошелек сохранен для пользователя {telegram_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения кошелька: {e}")
            return False
    
    def remove_wallet_address(self, telegram_id):
        """
        Удаляет адрес кошелька пользователя
        
        Args:
            telegram_id (int): ID пользователя
            
        Returns:
            bool: True если успешно удалено
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET wallet_address = NULL, last_activity = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            """, (telegram_id,))
            
            conn.commit()
            conn.close()
            
            # Обновляем статистику пользователя
            self.update_user_stats(telegram_id)
            
            logger.info(f"Кошелек удален для пользователя {telegram_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления кошелька: {e}")
            return False
    
    def get_wallet_address(self, telegram_id):
        """
        Получает адрес кошелька пользователя
        
        Args:
            telegram_id (int): ID пользователя
            
        Returns:
            str: Адрес кошелька или None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT wallet_address 
                FROM users 
                WHERE telegram_id = ?
            """, (telegram_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] else None
            
        except Exception as e:
            logger.error(f"Ошибка получения кошелька: {e}")
            return None
    
    def is_admin(self, telegram_id):
        """
        Проверяет, является ли пользователь админом
        
        Args:
            telegram_id (int): ID пользователя
            
        Returns:
            bool: True если админ
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT is_admin 
                FROM users 
                WHERE telegram_id = ?
            """, (telegram_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return bool(result[0]) if result else False
            
        except Exception as e:
            logger.error(f"Ошибка проверки админа: {e}")
            return False

# Создаем глобальный экземпляр для использования в боте
db_manager = DatabaseManager()

# Функции для интеграции в основной бот
def update_user_statistics(user_id=None):
    """Обновляет статистику пользователя"""
    return db_manager.update_user_stats(user_id)

def get_user_full_info(telegram_id):
    """Получает полную информацию о пользователе"""
    return db_manager.get_user_info(telegram_id)

def save_wallet_address(telegram_id, wallet_address):
    """Сохраняет адрес кошелька"""
    return db_manager.save_wallet_address(telegram_id, wallet_address)

def remove_wallet_address(telegram_id):
    """Удаляет адрес кошелька"""
    return db_manager.remove_wallet_address(telegram_id)

def get_wallet_address(telegram_id):
    """Получает адрес кошелька"""
    return db_manager.get_wallet_address(telegram_id)

def is_admin(telegram_id):
    """Проверяет, является ли пользователь админом"""
    return db_manager.is_admin(telegram_id)

if __name__ == "__main__":
    # Тестируем функциональность
    print("🧪 Тестирование DatabaseManager...")
    
    # Обновляем статистику всех пользователей
    if update_user_statistics():
        print("✅ Статистика обновлена")
    
    # Получаем информацию о реальных пользователях
    real_users = [739935417, 798427688]
    
    for user_id in real_users:
        user_info = get_user_full_info(user_id)
        if user_info:
            print(f"\n👤 @{user_info['username']} ({user_info['first_name']})")
            print(f"   💳 Кошелек: {user_info['wallet_address'] or 'НЕ УКАЗАН'}")
            print(f"   👑 Админ: {'Да' if user_info['is_admin'] else 'Нет'}")
            print(f"   💰 Депозиты: {user_info['total_deposits']:.2f} USDT")
            print(f"   🎁 Заработано: {user_info['total_earned']:.2f} USDT")
            print(f"   💸 Выведено: {user_info['total_withdrawals']:.2f} USDT")
            print(f"   💵 Доступно: {user_info['available_balance']:.2f} USDT")





