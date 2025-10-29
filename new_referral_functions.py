#!/usr/bin/env python3
"""
Новые функции для 3-уровневой реферальной системы
"""

import sqlite3
import random
import string
from datetime import datetime

DATABASE_PATH = "bot_database.db"

class NewReferralSystem:
    """Новая 3-уровневая реферальная система"""
    
    def __init__(self):
        self.percentages = {
            '30_days': {1: 15.0, 2: 10.0, 3: 5.0},
            '10_days': {1: 5.0, 2: 3.0, 3: 1.5}
        }
    
    def generate_referral_code(self):
        """Генерировать уникальный реферальный код"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users WHERE referral_code = ?', (code,))
                if cursor.fetchone()[0] == 0:
                    return code
    
    def get_referral_code(self, user_id):
        """Получить реферальный код пользователя"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT referral_code FROM users WHERE telegram_id = ?', (user_id,))
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            else:
                # Генерируем новый код
                code = self.generate_referral_code()
                cursor.execute('UPDATE users SET referral_code = ? WHERE telegram_id = ?', (code, user_id))
                conn.commit()
                return code
    
    def process_referral_join(self, user_id, referral_code):
        """Обработать присоединение по реферальной ссылке"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Находим реферера по коду
            cursor.execute('SELECT telegram_id FROM users WHERE referral_code = ?', (referral_code,))
            referrer_result = cursor.fetchone()
            
            if not referrer_result:
                return False, "Неверный реферальный код"
            
            referrer_id = referrer_result[0]
            
            if referrer_id == user_id:
                return False, "Нельзя пригласить самого себя"
            
            # Проверяем, не приглашен ли уже этот пользователь
            cursor.execute('SELECT COUNT(*) FROM referral_network WHERE referred_id = ?', (user_id,))
            if cursor.fetchone()[0] > 0:
                return False, "Вы уже приглашены в систему"
            
            # Создаем связь 1-го уровня
            cursor.execute('''
                INSERT INTO referral_network (referrer_id, referred_id, level)
                VALUES (?, ?, 1)
            ''', (referrer_id, user_id))
            
            # Обновляем referrer_id в таблице users
            cursor.execute('UPDATE users SET referrer_id = ? WHERE telegram_id = ?', (referrer_id, user_id))
            
            # Создаем реферальный баланс если его нет
            cursor.execute('''
                INSERT OR IGNORE INTO referral_balances (user_id, balance, total_earned, total_withdrawn)
                VALUES (?, 0.0, 0.0, 0.0)
            ''', (user_id,))
            
            # Создаем связи 2-го и 3-го уровней
            self._create_multi_level_connections(referrer_id, user_id)
            
            conn.commit()
            return True, f"Вы успешно присоединились по приглашению!"
    
    def _create_multi_level_connections(self, referrer_id, new_user_id):
        """Создать многоуровневые связи"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Создаем связи 2-го уровня (рефереры реферера)
            cursor.execute('''
                INSERT OR IGNORE INTO referral_network (referrer_id, referred_id, level)
                SELECT referrer_id, ?, 2
                FROM referral_network 
                WHERE referred_id = ? AND level = 1
            ''', (new_user_id, referrer_id))
            
            # Создаем связи 3-го уровня (рефереры рефереров реферера)
            cursor.execute('''
                INSERT OR IGNORE INTO referral_network (referrer_id, referred_id, level)
                SELECT rn1.referrer_id, ?, 3
                FROM referral_network rn1
                JOIN referral_network rn2 ON rn1.referred_id = rn2.referrer_id
                WHERE rn2.referred_id = ? AND rn1.level = 1 AND rn2.level = 1
            ''', (new_user_id, referrer_id))
            
            conn.commit()
    
    def process_deposit_referral_rewards(self, deposit_id, user_id, amount, deposit_type):
        """Обработать реферальные вознаграждения при создании депозита"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Получаем проценты для данного типа депозита
            percentages = self.percentages.get(deposit_type, {})
            
            # Находим всех рефереров этого пользователя
            cursor.execute('''
                SELECT referrer_id, level FROM referral_network 
                WHERE referred_id = ?
            ''', (user_id,))
            
            referrers = cursor.fetchall()
            
            total_rewards = 0
            for referrer_id, level in referrers:
                if level in percentages:
                    # Рассчитываем сумму вознаграждения
                    reward_amount = amount * (percentages[level] / 100)
                    total_rewards += reward_amount
                    
                    # Обновляем баланс реферера
                    cursor.execute('''
                        UPDATE referral_balances 
                        SET balance = balance + ?, total_earned = total_earned + ?
                        WHERE user_id = ?
                    ''', (reward_amount, reward_amount, referrer_id))
                    
                    # Создаем запись в истории транзакций
                    cursor.execute('''
                        INSERT INTO referral_transactions 
                        (user_id, amount, transaction_type, source_deposit_id, source_user_id, level, description)
                        VALUES (?, ?, 'earned', ?, ?, ?, ?)
                    ''', (referrer_id, reward_amount, deposit_id, user_id, level, 
                          f"Реферальное вознаграждение {level}-го уровня с депозита #{deposit_id}"))
            
            conn.commit()
            return total_rewards
    
    def get_user_referral_balance(self, user_id):
        """Получить реферальный баланс пользователя"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT balance, total_earned, total_withdrawn 
                FROM referral_balances 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'balance': result[0],
                    'total_earned': result[1],
                    'total_withdrawn': result[2]
                }
            else:
                # Создаем баланс если его нет
                cursor.execute('''
                    INSERT INTO referral_balances (user_id, balance, total_earned, total_withdrawn)
                    VALUES (?, 0.0, 0.0, 0.0)
                ''', (user_id,))
                conn.commit()
                return {'balance': 0.0, 'total_earned': 0.0, 'total_withdrawn': 0.0}
    
    def get_user_referral_stats(self, user_id):
        """Получить статистику рефералов пользователя"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Количество рефералов по уровням
            cursor.execute('''
                SELECT level, COUNT(*) 
                FROM referral_network 
                WHERE referrer_id = ?
                GROUP BY level
            ''', (user_id,))
            
            level_stats = {1: 0, 2: 0, 3: 0}
            for level, count in cursor.fetchall():
                level_stats[level] = count
            
            # Общая статистика
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_referrals,
                    SUM(CASE WHEN level = 1 THEN 1 ELSE 0 END) as level1,
                    SUM(CASE WHEN level = 2 THEN 1 ELSE 0 END) as level2,
                    SUM(CASE WHEN level = 3 THEN 1 ELSE 0 END) as level3
                FROM referral_network 
                WHERE referrer_id = ?
            ''', (user_id,))
            
            total_stats = cursor.fetchone()
            
            return {
                'total_referrals': total_stats[0] if total_stats else 0,
                'level1': level_stats[1],
                'level2': level_stats[2],
                'level3': level_stats[3]
            }
    
    def create_withdrawal_request(self, user_id, amount, wallet_address):
        """Создать заявку на вывод реферальных средств"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Проверяем баланс
            balance_info = self.get_user_referral_balance(user_id)
            if amount > balance_info['balance']:
                return False, "Недостаточно средств на балансе"
            
            if amount <= 0:
                return False, "Сумма должна быть больше 0"
            
            # Создаем заявку на вывод
            cursor.execute('''
                INSERT INTO referral_withdrawals (user_id, amount, wallet_address, status)
                VALUES (?, ?, ?, 'pending')
            ''', (user_id, amount, wallet_address))
            
            conn.commit()
            return True, "Заявка на вывод создана"
    
    def get_pending_withdrawals(self):
        """Получить ожидающие заявки на вывод"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT rw.id, rw.user_id, rw.amount, rw.wallet_address, rw.created_at,
                       u.first_name, u.username
                FROM referral_withdrawals rw
                JOIN users u ON rw.user_id = u.telegram_id
                WHERE rw.status = 'pending'
                ORDER BY rw.created_at ASC
            ''')
            
            return cursor.fetchall()
    
    def process_withdrawal(self, withdrawal_id, admin_id):
        """Обработать заявку на вывод"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Получаем данные заявки
            cursor.execute('''
                SELECT user_id, amount FROM referral_withdrawals 
                WHERE id = ? AND status = 'pending'
            ''', (withdrawal_id,))
            
            result = cursor.fetchone()
            if not result:
                return False, "Заявка не найдена"
            
            user_id, amount = result
            
            # Проверяем баланс
            balance_info = self.get_user_referral_balance(user_id)
            if amount > balance_info['balance']:
                return False, "Недостаточно средств"
            
            # Создаем транзакцию
            cursor.execute('''
                INSERT INTO transactions (telegram_id, amount, status, created_at)
                VALUES (?, ?, 'completed', CURRENT_TIMESTAMP)
            ''', (user_id, amount))
            
            transaction_id = cursor.lastrowid
            
            # Обновляем баланс
            cursor.execute('''
                UPDATE referral_balances 
                SET balance = balance - ?, total_withdrawn = total_withdrawn + ?
                WHERE user_id = ?
            ''', (amount, amount, user_id))
            
            # Обновляем статус заявки
            cursor.execute('''
                UPDATE referral_withdrawals 
                SET status = 'completed', transaction_id = ?, processed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (transaction_id, withdrawal_id))
            
            # Создаем запись в истории транзакций
            cursor.execute('''
                INSERT INTO referral_transactions 
                (user_id, amount, transaction_type, description)
                VALUES (?, ?, 'withdrawn', 'Вывод реферальных средств')
            ''', (user_id, amount))
            
            conn.commit()
            return True, "Выплата обработана"

# Пример использования
if __name__ == "__main__":
    system = NewReferralSystem()
    
    # Тестируем функции
    print("🧪 ТЕСТИРОВАНИЕ НОВОЙ РЕФЕРАЛЬНОЙ СИСТЕМЫ")
    print("=" * 50)
    
    # Получаем реферальный код для пользователя
    test_user_id = 123456789
    code = system.get_referral_code(test_user_id)
    print(f"Реферальный код пользователя {test_user_id}: {code}")
    
    # Получаем статистику
    stats = system.get_user_referral_stats(test_user_id)
    print(f"Статистика рефералов: {stats}")
    
    # Получаем баланс
    balance = system.get_user_referral_balance(test_user_id)
    print(f"Баланс: {balance}")
    
    # Получаем ожидающие заявки
    pending = system.get_pending_withdrawals()
    print(f"Ожидающие заявки: {len(pending)}")
    
    print("\n✅ Система готова к работе!")






