#!/usr/bin/env python3
"""
ФондКлик - Telegram Crypto Payment Bot
Платформа для управления цифровыми активами
"""

import logging
import sqlite3
import hashlib
import asyncio
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
# Убираем зависимость от crypto_bot

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8204117323:AAEe4-1jEKpSkpr13-FYjdSdFeBdbQHpNcY"
DATABASE_PATH = "bot_database.db"
CRYPTO_BOT_TOKEN = "469004:AAFOCI5N0HAQg3RbUKynaRO0cSzADVj0x8R"

# Реферальная система - проценты по уровням
REFERRAL_PERCENTAGES = {
    1: 10.0,  # 10% с рефералов 1 уровня
    2: 6.0,   # 6% с рефералов 2 уровня
    3: 5.0,   # 5% с рефералов 3 уровня
    4: 4.0,   # 4% с рефералов 4 уровня
    5: 3.0,   # 3% с рефералов 5 уровня
    6: 2.0    # 2% с рефералов 6 уровня
}
MAX_REFERRAL_LEVEL = 6

class CryptoBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.init_database()
        self.setup_handlers()
        # Словарь для хранения ID сообщений пользователей
        self.user_messages = {}
    
    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    referral_code TEXT UNIQUE,
                    referred_by TEXT,
                    wallet_address TEXT,
                    balance REAL DEFAULT 0.0,
                    total_earned REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица реферальных связей (для многоуровневой системы)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referral_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (referred_id) REFERENCES users (telegram_id)
                )
            ''')
            
            # Таблица реферальных выплат
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referral_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    percentage REAL NOT NULL,
                    transaction_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (referred_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (transaction_id) REFERENCES transactions (id)
                )
            ''')
            
            # Таблица транзакций
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USDT',
                    status TEXT DEFAULT 'pending',
                    wallet_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                )
            ''')
            
            # Таблица администраторов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица заявок на вывод
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS withdrawal_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    wallet_address TEXT,
                    status TEXT DEFAULT 'pending',
                    admin_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
                )
            ''')
            
            # Таблица выплат вкладов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deposit_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    original_amount REAL,
                    return_amount REAL,
                    payment_date DATE,
                    days_remaining INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP,
                    paid_by INTEGER,
                    deposit_type TEXT,
                    wallet_address TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
            ''')
            
            conn.commit()
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("addadmin", self.add_admin_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        
        # Добавляем обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Ошибка: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже или используйте /menu"
            )
    
    def get_or_create_user(self, telegram_id, username=None, first_name=None, last_name=None):
        """Получить или создать пользователя"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Проверяем существование пользователя
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            user = cursor.fetchone()
            
            if user:
                # Обновляем данные
                cursor.execute('''
                    UPDATE users SET username = ?, first_name = ?, last_name = ?
                    WHERE telegram_id = ?
                ''', (username, first_name, last_name, telegram_id))
                conn.commit()
                
                # Получаем обновленные данные
                cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
                user = cursor.fetchone()
            else:
                # Создаем нового пользователя
                referral_code = self.generate_referral_code(telegram_id)
                cursor.execute('''
                    INSERT INTO users (telegram_id, username, first_name, last_name, referral_code)
                    VALUES (?, ?, ?, ?, ?)
                ''', (telegram_id, username, first_name, last_name, referral_code))
                conn.commit()
                
                # Получаем созданного пользователя
                cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
                user = cursor.fetchone()
            
            # Преобразуем в словарь
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, user))
    
    def generate_referral_code(self, telegram_id):
        """Генерирует реферальный код"""
        unique_string = f"{telegram_id}_{datetime.now().timestamp()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:8].upper()
    
    def get_user_by_referral_code(self, referral_code):
        """Найти пользователя по реферальному коду"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE referral_code = ?', (referral_code,))
            user = cursor.fetchone()
            
            if user:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, user))
            return None
    
    def set_referred_by(self, telegram_id, referral_code):
        """Установить реферала и создать многоуровневые связи"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Находим реферера по коду
            referrer = cursor.execute('''
                SELECT telegram_id FROM users WHERE referral_code = ?
            ''', (referral_code,)).fetchone()
            
            if not referrer:
                return False
            
            referrer_id = referrer[0]
            
            # Обновляем основную связь
            cursor.execute('''
                UPDATE users 
                SET referred_by = ?
                WHERE telegram_id = ?
            ''', (referral_code, telegram_id))
            
            # Создаем многоуровневые связи
            self._create_referral_relations(cursor, referrer_id, telegram_id, 1)
            
            conn.commit()
            return True
    
    def _create_referral_relations(self, cursor, referrer_id: int, referred_id: int, level: int):
        """Создать реферальные связи для всех уровней"""
        if level > MAX_REFERRAL_LEVEL:
            return
        
        # Создаем связь текущего уровня
        cursor.execute('''
            INSERT INTO referral_relations (referrer_id, referred_id, level)
            VALUES (?, ?, ?)
        ''', (referrer_id, referred_id, level))
        
        # Находим реферера текущего реферера для следующего уровня
        parent_referrer = cursor.execute('''
            SELECT referred_by FROM users WHERE telegram_id = ?
        ''', (referrer_id,)).fetchone()
        
        if parent_referrer and parent_referrer[0]:
            # Находим ID родительского реферера
            parent_id = cursor.execute('''
                SELECT telegram_id FROM users WHERE referral_code = ?
            ''', (parent_referrer[0],)).fetchone()
            
            if parent_id:
                # Рекурсивно создаем связи для следующих уровней
                self._create_referral_relations(cursor, parent_id[0], referred_id, level + 1)
    
    def get_referral_stats(self, telegram_id: int) -> dict:
        """Получить статистику рефералов по уровням"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            stats = {}
            total_referrals = 0
            
            for level in range(1, MAX_REFERRAL_LEVEL + 1):
                count = cursor.execute('''
                    SELECT COUNT(*) FROM referral_relations 
                    WHERE referrer_id = ? AND level = ?
                ''', (telegram_id, level)).fetchone()[0]
                
                stats[f'level_{level}'] = count
                total_referrals += count
            
            stats['total'] = total_referrals
            return stats
    
    def process_referral_payments(self, referred_id: int, amount: float, transaction_id: int):
        """Обработать реферальные выплаты для всех уровней"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Получаем всех рефереров по уровням
            referrers = cursor.execute('''
                SELECT referrer_id, level FROM referral_relations 
                WHERE referred_id = ?
                ORDER BY level
            ''', (referred_id,)).fetchall()
            
            total_paid = 0
            
            for referrer_id, level in referrers:
                if level in REFERRAL_PERCENTAGES:
                    percentage = REFERRAL_PERCENTAGES[level]
                    referral_amount = (amount * percentage) / 100
                    
                    # Начисляем реферальную выплату
                    cursor.execute('''
                        UPDATE users 
                        SET balance = balance + ?, total_earned = total_earned + ?
                        WHERE telegram_id = ?
                    ''', (referral_amount, referral_amount, referrer_id))
                    
                    # Записываем реферальную выплату
                    cursor.execute('''
                        INSERT INTO referral_payments 
                        (referrer_id, referred_id, level, amount, percentage, transaction_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (referrer_id, referred_id, level, referral_amount, percentage, transaction_id))
                    
                    total_paid += referral_amount
                    
                    logger.info(f"Реферальная выплата: {referral_amount:.2f} USDT (уровень {level}, {percentage}%) для пользователя {referrer_id}")
            
            conn.commit()
            return total_paid
    
    def update_wallet_address(self, telegram_id, wallet_address):
        """Обновить адрес кошелька"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET wallet_address = ? WHERE telegram_id = ?', (wallet_address, telegram_id))
            conn.commit()
    
    def create_transaction(self, telegram_id, amount, wallet_address):
        """Создать транзакцию"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (telegram_id, amount, wallet_address)
                VALUES (?, ?, ?)
            ''', (telegram_id, amount, wallet_address))
            transaction_id = cursor.lastrowid
            conn.commit()
            return transaction_id
    
    def get_user_transactions(self, telegram_id):
        """Получить транзакции пользователя"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE telegram_id = ? 
                ORDER BY created_at DESC
            ''', (telegram_id,))
            
            transactions = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, transaction)) for transaction in transactions]
    
    def update_transaction_status(self, transaction_id, status):
        """Обновить статус транзакции"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions 
                SET status = ?
                WHERE id = ?
            ''', (status, transaction_id))
            conn.commit()
    
    def update_user_balance(self, telegram_id, amount, transaction_id=None):
        """Обновить баланс пользователя и обработать реферальные выплаты"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET balance = balance + ?
                WHERE telegram_id = ?
            ''', (amount, telegram_id))
            conn.commit()
        
        # Обрабатываем реферальные выплаты
        if transaction_id:
            total_referral_paid = self.process_referral_payments(telegram_id, amount, transaction_id)
            logger.info(f"Обработано реферальных выплат: {total_referral_paid:.2f} USDT для транзакции {transaction_id}")
    
    async def cleanup_old_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить только последние 5 сообщений для ускорения"""
        chat_id = update.effective_chat.id
        
        try:
            # Удаляем только последние 5 сообщений для ускорения
            current_message_id = update.effective_message.message_id if update.effective_message else 0
            
            # Удаляем только последние 5 сообщений
            for message_id in range(max(1, current_message_id - 5), current_message_id):
                try:
                    await context.bot.delete_message(chat_id, message_id)
                except Exception:
                    # Игнорируем ошибки
                    pass
            
        except Exception as e:
            logger.error(f"Ошибка при очистке чата {chat_id}: {e}")
    
    async def cleanup_all_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить ВСЕ сообщения в чате (включая сообщения всех участников)"""
        chat_id = update.effective_chat.id
        
        try:
            # Проверяем, является ли бот администратором
            bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                logger.warning(f"Бот не является администратором в чате {chat_id}")
                return False
            
            # Получаем ВСЕ сообщения из истории чата (до 1000)
            messages = []
            async for message in context.bot.get_chat_history(chat_id, limit=1000):
                messages.append(message.message_id)
            
            # Удаляем все сообщения
            deleted_count = 0
            for message_id in messages:
                try:
                    await context.bot.delete_message(chat_id, message_id)
                    deleted_count += 1
                    # Небольшая задержка, чтобы не превысить лимиты API
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.debug(f"Не удалось удалить сообщение {message_id}: {e}")
            
            logger.info(f"Удалено {deleted_count} сообщений в чате {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при очистке чата {chat_id}: {e}")
            return False
    
    async def track_message(self, update: Update, message_id: int):
        """Отслеживать сообщение пользователя"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        # Добавляем новое сообщение в список
        self.user_messages[user_id].append(message_id)
        
        # Ограничиваем количество сообщений (оставляем только последние 3)
        if len(self.user_messages[user_id]) > 3:
            old_message_id = self.user_messages[user_id].pop(0)
            try:
                await update.get_bot().delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=old_message_id
                )
            except Exception as e:
                logger.debug(f"Не удалось удалить старое сообщение {old_message_id}: {e}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        message = update.message
        
        # Получаем или создаем пользователя
        user_data = self.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Проверяем реферальный код (анонимно)
        if context.args:
            referral_code = context.args[0]
            if referral_code != user_data['referral_code']:
                referred_user = self.get_user_by_referral_code(referral_code)
                if referred_user:
                    self.set_referred_by(user.id, referral_code)
                    # Регистрация по реферальной ссылке происходит анонимно
        
        # Показываем главное меню
        await self.show_main_menu(update, context)
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /menu"""
        await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        user = update.effective_user
        user_data = self.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Создаем клавиатуру
        keyboard = [
            [InlineKeyboardButton("💰 Внести средства", callback_data="deposit")],
            [InlineKeyboardButton("📊 Мои транзакции", callback_data="transactions")],
            [InlineKeyboardButton("👥 Реферальная система", callback_data="referral_system")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Формируем сообщение
        message_text = f"""
🎯 ФондКлик

ФондКлик — это платформа для управления цифровыми активами, где пользователи могут размещать краткосрочные депозиты с фиксированной доходностью.

Пул из размещенных вкладов используется в работе нескольких проектов, прибыль от которых распределяется между пользователями, предоставившими свои средства.

Для начала работы выберите нужную опцию ниже.
        """
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            sent_message = await update.message.reply_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            # Отслеживаем новое сообщение
            await self.track_message(update, sent_message.message_id)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "deposit":
            await self.show_deposit_menu(update, context)
        elif data == "transactions":
            await self.show_transactions(update, context)
        elif data == "help":
            await self.show_help(update, context)
        elif data == "referral_system":
            await self.show_referral_system(update, context)
        elif data == "back_to_menu":
            await self.show_main_menu(update, context)
        elif data == "confirm_wallet":
            await self.show_amount_selection(update, context)
        elif data.startswith("amount_"):
            amount = data.split("_")[1]
            await self.process_deposit_amount(update, context, amount)
        elif data == "confirm_payment":
            await self.show_payment_info(update, context)
        elif data == "check_payment":
            await self.check_payment_status(update, context)
    
    async def show_deposit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню пополнения"""
        user = update.effective_user
        user_data = self.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        if not user_data['wallet_address']:
            # Просим ввести адрес кошелька
            context.user_data['waiting_for_wallet'] = True
            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                text="💳 Введите адрес вашего USDT кошелька (TRC20):",
                reply_markup=reply_markup
            )
        else:
            # Показываем выбор суммы
            await self.show_amount_selection(update, context)
    
    async def show_amount_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать выбор суммы"""
        user = update.effective_user
        user_data = self.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        keyboard = [
            [InlineKeyboardButton("10 USDT", callback_data="amount_10")],
            [InlineKeyboardButton("25 USDT", callback_data="amount_25")],
            [InlineKeyboardButton("50 USDT", callback_data="amount_50")],
            [InlineKeyboardButton("100 USDT", callback_data="amount_100")],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = f"""
💰 Пополнение баланса

💳 Ваш кошелек: `{user_data['wallet_address']}`
💵 Выберите сумму для пополнения:
        """
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def process_deposit_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE, amount: str):
        """Обработка выбранной суммы"""
        user = update.effective_user
        user_data = self.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Создаем транзакцию
        transaction_id = self.create_transaction(
            telegram_id=user.id,
            amount=float(amount),
            wallet_address=user_data['wallet_address']
        )
        
        # Сохраняем данные транзакции
        context.user_data['current_transaction_id'] = transaction_id
        context.user_data['deposit_amount'] = float(amount)
        
        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить платеж", callback_data="confirm_payment")],
            [InlineKeyboardButton("🔙 Назад", callback_data="deposit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = f"""
💳 Подтверждение платежа

💰 Сумма: {amount} USDT
💳 Кошелек: `{user_data['wallet_address']}`
🆔 ID транзакции: {transaction_id}

⚠️ После подтверждения вы будете перенаправлены к крипто-боту для оплаты.
        """
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_payment_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать информацию о платеже"""
        amount = context.user_data.get('deposit_amount', 0)
        transaction_id = context.user_data.get('current_transaction_id')
        
        # Устанавливаем токен для CryptoBot
        import crypto_bot
        crypto_bot.CRYPTO_BOT_TOKEN = CRYPTO_BOT_TOKEN
        
        # Создаем счет через CryptoBot
        invoice_data = await create_invoice(
            amount=float(amount),
            currency="USDT",
            description=f"Пополнение баланса - Транзакция #{transaction_id}"
        )
        
        if invoice_data:
            # Сохраняем ID счета для отслеживания
            context.user_data['invoice_id'] = invoice_data['invoice_id']
            
            keyboard = [
                [InlineKeyboardButton("💳 Оплатить", url=invoice_data['pay_url'])],
                [InlineKeyboardButton("🔄 Проверить статус", callback_data="check_payment")],
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = f"""
🤖 Крипто-платеж

💰 Сумма: {amount} USDT
🆔 ID транзакции: {transaction_id}
📋 ID счета: {invoice_data['invoice_id']}

💳 Нажмите кнопку "Оплатить" для перехода к оплате
⏰ Счет действителен 15 минут
            """
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = f"""
❌ Ошибка создания счета

💰 Сумма: {amount} USDT
🆔 ID транзакции: {transaction_id}

⚠️ Не удалось создать счет для оплаты. Попробуйте позже.
            """
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    async def check_payment_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверить статус платежа"""
        invoice_id = context.user_data.get('invoice_id')
        transaction_id = context.user_data.get('current_transaction_id')
        
        if not invoice_id:
            await update.callback_query.answer("❌ Нет активного счета для проверки")
            return
        
        # Устанавливаем токен для CryptoBot
        import crypto_bot
        crypto_bot.CRYPTO_BOT_TOKEN = CRYPTO_BOT_TOKEN
        
        # Проверяем статус через CryptoBot
        status = await check_payment_status(invoice_id)
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="check_payment")],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if status == "paid":
            # Платеж успешен
            self.update_transaction_status(transaction_id, "completed")
            
            # Обновляем баланс пользователя и обрабатываем реферальные выплаты
            user = update.effective_user
            amount = context.user_data.get('deposit_amount', 0)
            self.update_user_balance(user.id, amount, transaction_id)
            
            message_text = f"""
✅ Платеж успешно завершен!

💰 Сумма: {amount} USDT
🆔 ID транзакции: {transaction_id}
📋 ID счета: {invoice_id}

💳 Средства зачислены на ваш баланс
            """
            
            # Очищаем данные транзакции
            context.user_data.pop('invoice_id', None)
            context.user_data.pop('current_transaction_id', None)
            context.user_data.pop('deposit_amount', None)
            
        elif status == "active":
            message_text = f"""
⏳ Ожидание платежа

💰 Сумма: {context.user_data.get('deposit_amount', 0)} USDT
🆔 ID транзакции: {transaction_id}
📋 ID счета: {invoice_id}

💳 Счет ожидает оплаты
            """
        elif status == "expired":
            message_text = f"""
❌ Счет истек

💰 Сумма: {context.user_data.get('deposit_amount', 0)} USDT
🆔 ID транзакции: {transaction_id}
📋 ID счета: {invoice_id}

⏰ Время действия счета истекло. Создайте новый платеж.
            """
            
            # Обновляем статус транзакции
            self.update_transaction_status(transaction_id, "failed")
            
        else:
            message_text = f"""
❌ Ошибка проверки статуса

💰 Сумма: {context.user_data.get('deposit_amount', 0)} USDT
🆔 ID транзакции: {transaction_id}

⚠️ Не удалось проверить статус платежа
            """
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    async def show_transactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать историю транзакций"""
        user = update.effective_user
        transactions = self.get_user_transactions(user.id)
        
        if not transactions:
            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                text="📊 У вас пока нет транзакций",
                reply_markup=reply_markup
            )
            return
        
        message_text = "📊 История транзакций:\n\n"
        for transaction in transactions[:10]:
            status_emoji = {
                'pending': '⏳',
                'completed': '✅',
                'failed': '❌'
            }.get(transaction['status'], '❓')
            
            message_text += f"""
{status_emoji} {transaction['amount']} {transaction['currency']}
📅 {transaction['created_at']}
🆔 ID: {transaction['id']}
            """
        
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать справку"""
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = """
ℹ️ Справка - ФондКлик

🎯 Этот бот позволяет:
• Размещать депозиты через USDT
• Участвовать в реферальной программе
• Отслеживать историю транзакций

🔗 Реферальная программа:
• Приглашайте друзей по вашей ссылке
• Получайте бонусы за каждого реферала

❓ Если у вас есть вопросы, обратитесь к администратору.
        """
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    async def show_referral_system(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать упрощенную информацию о реферальной системе"""
        user = update.effective_user
        
        # Получаем только базовую статистику
        referral_stats = self.get_referral_stats(user.id)
        
        # Получаем суммарный доход
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            total_earned = cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM referral_payments 
                WHERE referrer_id = ?
            ''', (user.id,)).fetchone()[0] or 0
        
        # Получаем реферальный код
        user_data = self.get_user_by_telegram_id(user.id)
        referral_code = user_data['referral_code'] if user_data else "unknown"
        
        # Формируем компактное сообщение
        referral_link = f"https://t.me/{context.bot.username}?start={referral_code}"
        message_text = f"""
👥 РЕФЕРАЛЬНАЯ СИСТЕМА

🔗 Ваша ссылка: `{referral_link}`

📊 Рефералы: 1-й: {referral_stats['level_1']} | 2-й: {referral_stats['level_2']} | 3-й: {referral_stats['level_3']} | 4-й: {referral_stats['level_4']} | 5-й: {referral_stats['level_5']} | 6-й: {referral_stats['level_6']}

💰 Всего: {referral_stats['total']} чел. | Доход: {total_earned:.2f} USDT

💡 Приглашайте по ссылке → получайте % с пополнений до 6 уровня
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        message = update.message
        
        if context.user_data.get('waiting_for_wallet'):
            # Пользователь вводит адрес кошелька
            wallet_address = message.text.strip()
            
            # Простая валидация адреса USDT (TRC20)
            if len(wallet_address) >= 34 and wallet_address.startswith('T'):
                # Сохраняем адрес кошелька
                self.update_wallet_address(user.id, wallet_address)
                context.user_data['waiting_for_wallet'] = False
                
                # Показываем подтверждение
                keyboard = [
                    [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_wallet")],
                    [InlineKeyboardButton("✏️ Изменить", callback_data="deposit")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                sent_message = await message.reply_text(
                    f"💳 Адрес кошелька: `{wallet_address}`\n\nПодтвердите правильность адреса:",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                # Отслеживаем новое сообщение
                await self.track_message(update, sent_message.message_id)
            else:
                sent_message = await message.reply_text(
                    "❌ Неверный формат адреса USDT (TRC20). Адрес должен начинаться с 'T' и содержать не менее 34 символов."
                )
                # Отслеживаем новое сообщение
                await self.track_message(update, sent_message.message_id)
        else:
            # Неизвестное сообщение
            sent_message = await message.reply_text(
                "🤖 Используйте кнопки меню для навигации или команду /menu"
            )
            # Отслеживаем новое сообщение
            await self.track_message(update, sent_message.message_id)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фотографий"""
        user = update.effective_user
        message = update.message
        
        # Получаем информацию о фото
        photo = message.photo[-1]  # Берем фото наивысшего качества
        
        sent_message = await message.reply_text(
            f"📸 Спасибо за фото! Размер: {photo.width}x{photo.height}\n\n"
            "🤖 Используйте кнопки меню для навигации или команду /menu"
        )
        
        # Отслеживаем новое сообщение
        await self.track_message(update, sent_message.message_id)
    
    def _acquire_lock(self):
        """Получить блокировку файла для предотвращения множественного запуска"""
        try:
            import fcntl
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            return True
        except (IOError, OSError):
            return False
    
    def _release_lock(self):
        """Освободить блокировку файла"""
        if self.lock_fd:
            try:
                import fcntl
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
                os.unlink(self.lock_file)
            except:
                pass
            self.lock_fd = None

    def is_admin(self, telegram_id):
        """Проверить, является ли пользователь администратором"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            admin = cursor.execute('SELECT telegram_id FROM admins WHERE telegram_id = ?', (telegram_id,)).fetchone()
            return admin is not None
    
    def add_admin(self, telegram_id, username, first_name, last_name):
        """Добавить администратора"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO admins (telegram_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, username, first_name, last_name))
            conn.commit()
    
    async def add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для добавления администратора"""
        user = update.effective_user
        
        # Проверяем, является ли пользователь администратором
        if not self.is_admin(user.id):
            await update.message.reply_text("❌ У вас нет прав для добавления администраторов")
            return
        
        if not context.args:
            await update.message.reply_text("Использование: /addadmin <telegram_id>")
            return
        
        # Получаем telegram_id из аргументов
        try:
            admin_id = int(context.args[0])
            self.add_admin(admin_id, f"admin_{admin_id}", "Admin", "User")
            await update.message.reply_text(f"✅ Пользователь {admin_id} добавлен как администратор")
        except ValueError:
            await update.message.reply_text("❌ Неверный формат. Используйте: /addadmin <telegram_id>")
    
    def run(self):
        """Запуск бота"""
        logger.info("🤖 ЗАПУСК БОТА - ВЕРСИЯ: bot_fondklik.py (ФОНДКЛИК С АДМИНКОЙ)")
        try:
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            print(f"❌ Ошибка запуска бота: {e}")

def main():
    """Главная функция"""
    bot = CryptoBot()
    bot.run()

if __name__ == '__main__':
    main()