import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "payments.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных с необходимыми таблицами"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                wallet_address TEXT,
                auto_mode BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица ожидающих платежей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                currency TEXT,
                wallet_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица подтвержденных платежей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS confirmed_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                currency TEXT,
                transaction_hash TEXT UNIQUE,
                wallet_address TEXT,
                confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица отслеживаемых кошельков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracked_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address TEXT UNIQUE,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица пользовательских кошельков (множественные кошельки)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                wallet_address TEXT,
                wallet_name TEXT,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, wallet_address)
            )
        ''')
        
        # Таблица уведомлений о транзакциях
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                currency TEXT,
                transaction_hash TEXT,
                wallet_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица связей пользователей с активными кошельками
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_payment_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_wallet TEXT NOT NULL,
                active_wallet TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_wallet)
            )
        ''')
        
        # Таблица отслеживания платежей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_wallet TEXT NOT NULL,
                active_wallet TEXT NOT NULL,
                amount REAL NOT NULL,
                tx_hash TEXT NOT NULL,
                confirmed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int, username: str = None, wallet_address: str = None):
        """Добавить пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, wallet_address, auto_mode)
            VALUES (?, ?, ?, 0)
        ''', (user_id, username, wallet_address))
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'wallet_address': result[2],
                'auto_mode': bool(result[3]) if len(result) > 3 else False,
                'created_at': result[4] if len(result) > 4 else result[3]
            }
        return None
    
    def add_pending_payment(self, user_id: int, amount: float, currency: str, wallet_address: str):
        """Добавить ожидающий платеж"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pending_payments (user_id, amount, currency, wallet_address)
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, currency, wallet_address))
        
        payment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return payment_id
    
    def get_pending_payments(self, wallet_address: str) -> List[Dict]:
        """Получить ожидающие платежи для кошелька"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM pending_payments 
            WHERE wallet_address = ? AND status = 'pending'
        ''', (wallet_address,))
        
        results = cursor.fetchall()
        conn.close()
        
        payments = []
        for result in results:
            payments.append({
                'id': result[0],
                'user_id': result[1],
                'amount': result[2],
                'currency': result[3],
                'wallet_address': result[4],
                'created_at': result[5],
                'status': result[6]
            })
        
        return payments
    
    def confirm_payment(self, user_id: int, amount: float, currency: str, 
                       transaction_hash: str, wallet_address: str):
        """Подтвердить платеж"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Дополнительная проверка: убеждаемся, что кошелек принадлежит пользователю
        cursor.execute('''
            SELECT COUNT(*) FROM user_wallets 
            WHERE user_id = ? AND wallet_address = ?
        ''', (user_id, wallet_address))
        
        wallet_exists = cursor.fetchone()[0] > 0
        if not wallet_exists:
            logger.warning(f"⚠️ Попытка подтвердить платеж на кошелек {wallet_address}, который не принадлежит пользователю {user_id}")
            conn.close()
            return False
        
        # Добавляем в подтвержденные платежи
        cursor.execute('''
            INSERT INTO confirmed_payments (user_id, amount, currency, transaction_hash, wallet_address)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, currency, transaction_hash, wallet_address))
        
        # Обновляем статус ожидающих платежей
        cursor.execute('''
            UPDATE pending_payments 
            SET status = 'confirmed' 
            WHERE user_id = ? AND amount = ? AND wallet_address = ? AND status = 'pending'
        ''', (user_id, amount, wallet_address))
        
        conn.commit()
        conn.close()
    
    def is_transaction_confirmed(self, transaction_hash: str) -> bool:
        """Проверить, была ли транзакция уже подтверждена"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM confirmed_payments 
            WHERE transaction_hash = ?
        ''', (transaction_hash,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def add_transaction_notification(self, user_id: int, amount: float, currency: str, 
                                   transaction_hash: str, wallet_address: str):
        """Добавить уведомление о транзакции"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transaction_notifications 
            (user_id, amount, currency, transaction_hash, wallet_address)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, currency, transaction_hash, wallet_address))
        
        conn.commit()
        conn.close()
    
    def get_user_notifications(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Получить уведомления пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, amount, currency, transaction_hash, wallet_address, 
                   created_at, is_read
            FROM transaction_notifications 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                'id': row[0],
                'amount': row[1],
                'currency': row[2],
                'transaction_hash': row[3],
                'wallet_address': row[4],
                'created_at': row[5],
                'is_read': bool(row[6])
            })
        
        conn.close()
        return notifications
    
    def mark_notification_as_read(self, notification_id: int):
        """Отметить уведомление как прочитанное"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE transaction_notifications 
            SET is_read = 1 
            WHERE id = ?
        ''', (notification_id,))
        
        conn.commit()
        conn.close()
    
    def get_unread_notifications_count(self, user_id: int) -> int:
        """Получить количество непрочитанных уведомлений"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM transaction_notifications 
            WHERE user_id = ? AND is_read = 0
        ''', (user_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_user_api_key(self, user_id: int) -> Optional[str]:
        """Получить API ключ пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT api_key FROM user_api_keys 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def save_user_api_key(self, user_id: int, api_key: str):
        """Сохранить API ключ пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создаем таблицу для API ключей если её нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_api_keys (
                user_id INTEGER PRIMARY KEY,
                api_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Сохраняем API ключ пользователя
        cursor.execute('''
            INSERT OR REPLACE INTO user_api_keys (user_id, api_key)
            VALUES (?, ?)
        ''', (user_id, api_key))
        
        conn.commit()
        conn.close()
    
    def add_tracked_wallet(self, wallet_address: str, user_id: int):
        """Добавить кошелек для отслеживания"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO tracked_wallets (wallet_address, user_id)
            VALUES (?, ?)
        ''', (wallet_address, user_id))
        
        conn.commit()
        conn.close()
    
    def get_tracked_wallets(self) -> List[Dict]:
        """Получить все отслеживаемые кошельки"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tracked_wallets')
        results = cursor.fetchall()
        conn.close()
        
        wallets = []
        for result in results:
            wallets.append({
                'id': result[0],
                'wallet_address': result[1],
                'user_id': result[2],
                'created_at': result[3]
            })
        
        return wallets
    
    def update_user_wallet(self, user_id: int, wallet_address: str):
        """Обновить кошелек пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET wallet_address = ? 
            WHERE user_id = ?
        ''', (wallet_address, user_id))
        
        conn.commit()
        conn.close()
    
    def update_user_auto_mode(self, user_id: int, auto_mode: bool):
        """Обновить автоматический режим пользователя"""
        import logging
        logger = logging.getLogger(__name__)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        logger.info(f"Обновление auto_mode для пользователя {user_id}: {auto_mode}")
        
        cursor.execute('''
            UPDATE users 
            SET auto_mode = ? 
            WHERE user_id = ?
        ''', (1 if auto_mode else 0, user_id))
        
        rows_affected = cursor.rowcount
        logger.info(f"Обновлено строк: {rows_affected}")
        
        # Проверяем, что обновилось
        cursor.execute('SELECT auto_mode FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            actual_value = bool(result[0])
            logger.info(f"Фактическое значение auto_mode в БД после обновления: {actual_value}")
        else:
            logger.warning(f"Пользователь {user_id} не найден в БД")
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Получить соединение с базой данных"""
        return sqlite3.connect(self.db_path)
    
    # Методы для работы с множественными кошельками
    def add_user_wallet(self, user_id: int, wallet_address: str, wallet_name: str = None):
        """Добавить кошелек пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if not wallet_name:
            wallet_name = f"Кошелек {wallet_address[:8]}..."
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_wallets (user_id, wallet_address, wallet_name, is_active)
            VALUES (?, ?, ?, 0)
        ''', (user_id, wallet_address, wallet_name))
        
        conn.commit()
        conn.close()
    
    def get_user_wallets(self, user_id: int) -> List[Dict]:
        """Получить все кошельки пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, wallet_address, wallet_name, is_active, created_at
            FROM user_wallets 
            WHERE user_id = ?
            ORDER BY is_active DESC, created_at DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        wallets = []
        for result in results:
            wallets.append({
                'id': result[0],
                'wallet_address': result[1],
                'wallet_name': result[2],
                'is_active': bool(result[3]),
                'created_at': result[4]
            })
        
        return wallets
    
    def set_active_wallet(self, user_id: int, wallet_id: int):
        """Установить активный кошелек"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Сначала снимаем активность со всех кошельков пользователя
        cursor.execute('''
            UPDATE user_wallets 
            SET is_active = 0 
            WHERE user_id = ?
        ''', (user_id,))
        
        # Затем устанавливаем активный кошелек
        cursor.execute('''
            UPDATE user_wallets 
            SET is_active = 1 
            WHERE id = ? AND user_id = ?
        ''', (wallet_id, user_id))
        
        conn.commit()
        conn.close()
    
    def delete_user_wallet(self, user_id: int, wallet_id: int):
        """Удалить кошелек пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM user_wallets 
            WHERE id = ? AND user_id = ?
        ''', (wallet_id, user_id))
        
        conn.commit()
        conn.close()
    
    def get_active_wallet(self, user_id: int) -> Optional[Dict]:
        """Получить активный кошелек пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, wallet_address, wallet_name, is_active, created_at
            FROM user_wallets 
            WHERE user_id = ? AND is_active = 1
            LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'wallet_address': result[1],
                'wallet_name': result[2],
                'is_active': bool(result[3]),
                'created_at': result[4]
            }
        return None
    
    def create_payment_link(self, user_wallet: str, active_wallet: str):
        """Создать связь между кошельком пользователя и активным кошельком"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_payment_links (user_wallet, active_wallet)
            VALUES (?, ?)
        ''', (user_wallet, active_wallet))
        
        conn.commit()
        conn.close()
        logger.info(f"Создана связь: {user_wallet} -> {active_wallet}")
    
    def get_active_wallet_for_user(self, user_wallet: str) -> Optional[str]:
        """Получить активный кошелек для кошелька пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT active_wallet FROM user_payment_links 
            WHERE user_wallet = ?
        ''', (user_wallet,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def add_payment_tracking(self, user_wallet: str, active_wallet: str, amount: float, tx_hash: str):
        """Добавить платеж в отслеживание"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO payment_tracking (user_wallet, active_wallet, amount, tx_hash)
            VALUES (?, ?, ?, ?)
        ''', (user_wallet, active_wallet, amount, tx_hash))
        
        conn.commit()
        conn.close()
        logger.info(f"Добавлен платеж в отслеживание: {user_wallet} -> {active_wallet}, {amount} USDT, {tx_hash}")
    
    def get_user_payments(self, user_wallet: str) -> List[Dict]:
        """Получить все платежи пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT amount, tx_hash, confirmed, created_at
            FROM payment_tracking 
            WHERE user_wallet = ?
            ORDER BY created_at DESC
        ''', (user_wallet,))
        
        payments = []
        for row in cursor.fetchall():
            payments.append({
                'amount': row[0],
                'tx_hash': row[1],
                'confirmed': bool(row[2]),
                'timestamp': row[3]
            })
        
        conn.close()
        return payments
    
    def mark_payment_confirmed(self, tx_hash: str):
        """Отметить платеж как подтвержденный"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE payment_tracking 
            SET confirmed = TRUE 
            WHERE tx_hash = ?
        ''', (tx_hash,))
        
        conn.commit()
        conn.close()
        logger.info(f"Платеж {tx_hash} отмечен как подтвержденный")

