import logging
import sqlite3
import hashlib
import asyncio
import aiohttp
import ssl
import os
import fcntl
import sys
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
# Импортируем систему проверки USDT платежей
from payment_verification_client import PaymentVerificationClient
from payment_config import USDT_PAYMENT_API_KEY, PAYMENT_VERIFICATION_URL, PAYMENT_WALLET

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8204117323:AAEe4-1jEKpSkpr13-FYjdSdFeBdbQHpNcY"
DATABASE_PATH = "bot_database.db"


class FastBot:
    def __init__(self):
        self.lock_file = "bot.lock"
        self.lock_fd = None

        # Проверяем, не запущен ли уже бот
        if not self._acquire_lock():
            print(
                "❌ Бот уже запущен! Остановите предыдущий экземпляр перед запуском нового.")
            print("💡 Используйте: pkill -f 'python3 bot_final.py'")
            sys.exit(1)

        self.application = Application.builder().token(BOT_TOKEN).build()

        # Инициализируем клиент проверки платежей
        self.payment_client = PaymentVerificationClient(
            api_key=USDT_PAYMENT_API_KEY,
            base_url=PAYMENT_VERIFICATION_URL
        )

        # Словарь для отслеживания ожидаемых платежей
        self.pending_payments = {}  # {user_wallet: {user_id, deposit_type, tracking_id}}

        # Словарь для сохранения ID сообщений с командой /start
        self.start_message_ids = {}  # {chat_id: message_id}

        # Загружаем сохраненные ID сообщений /start из базы данных
        self.load_start_message_ids()

        self.init_database()
        self.setup_handlers()

    def _acquire_lock(self):
        """Получить блокировку файла для предотвращения множественного запуска"""
        try:
            self.lock_fd = os.open(
                self.lock_file,
                os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (OSError, IOError):
            return False

    def _release_lock(self):
        """Освободить блокировку файла"""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                os.close(self.lock_fd)
                os.unlink(self.lock_file)
            except (OSError, IOError):
                pass

    def init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            # Простая таблица пользователей
            cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    referral_code TEXT UNIQUE,
    referred_by TEXT,
    balance REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
        ''')

            # Простая таблица рефералов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER,
    referred_id INTEGER,
    level INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
        ''')

        # Таблица для реферальных выплат
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER,
    referred_id INTEGER,
    level INTEGER,
    amount REAL,
    percentage REAL,
    transaction_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
        ''')

        # Таблица для отслеживания регистраций по ссылкам (всех, кто
        # перешел)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER,
    referred_id INTEGER,
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

        # Таблица администраторов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
    )
        ''')

        # Таблица транзакций пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    deposit_type TEXT,
    status TEXT DEFAULT 'pending',
    wallet_address TEXT,
    invoice_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
    )
        ''')

        # Создаем таблицу для сохранения ID сообщений /start
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS start_message_ids (
    chat_id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
        ''')

        conn.commit()

    def load_start_message_ids(self):
        """Загрузить сохраненные ID сообщений /start из базы данных"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT chat_id, message_id FROM start_message_ids')
                rows = cursor.fetchall()

                for chat_id, message_id in rows:
                    self.start_message_ids[chat_id] = message_id

            logger.info(
                f"Загружено {len(rows)} сохраненных ID сообщений /start")
        except Exception as e:
            logger.error(f"Ошибка загрузки ID сообщений /start: {e}")

    def save_start_message_id(self, chat_id: int, message_id: int):
        """Сохранить ID сообщения /start в базу данных"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO start_message_ids (chat_id, message_id, created_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (chat_id, message_id))
                conn.commit()

            # Обновляем словарь в памяти
            self.start_message_ids[chat_id] = message_id

            logger.info(
                f"Сохранен ID сообщения /start для чата {chat_id}: {message_id}")
        except Exception as e:
            logger.error(f"Ошибка сохранения ID сообщения /start: {e}")

    def setup_handlers(self):
    """Настройка обработчиков"""
    self.application.add_handler(
        CommandHandler(
            "start", self.start_command))
    self.application.add_handler(CommandHandler("menu", self.menu_command))
    self.application.add_handler(
        CommandHandler(
            "addadmin",
            self.add_admin_command))
    self.application.add_handler(
        CallbackQueryHandler(
            self.button_callback))
    self.application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message))

    def get_or_create_user(
            self,
            telegram_id,
            username,
            first_name,
            last_name):
    """Быстро получить или создать пользователя"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Проверяем существование
        user = cursor.execute('''
    SELECT * FROM users WHERE telegram_id = ?
        ''', (telegram_id,)).fetchone()

        if user:
    return {
        'telegram_id': user[0],
        'username': user[1],
        'first_name': user[2],
        'last_name': user[3],
        'referral_code': user[4],
        'referred_by': user[5],
        'balance': user[6]
    }

    # Создаем нового пользователя
    referral_code = hashlib.md5(
        f"{telegram_id}{
            datetime.now()}".encode()).hexdigest()[
        :8]

    cursor.execute('''
    INSERT INTO users (telegram_id, username, first_name, last_name, referral_code)
    VALUES (?, ?, ?, ?, ?)
        ''', (telegram_id, username, first_name, last_name, referral_code))

    conn.commit()

    return {
        'telegram_id': telegram_id,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'referral_code': referral_code,
        'referred_by': None,
        'balance': 0.0
    }

    def get_referral_stats(self, telegram_id):
    """Быстро получить статистику рефералов"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        stats = {}
        for level in range(1, 7):
    count = cursor.execute('''
    SELECT COUNT(*) FROM referral_relations
    WHERE referrer_id = ? AND level = ?
    ''', (telegram_id, level)).fetchone()[0]
    stats[f'level_{level}'] = count

    stats['total'] = sum(stats.values())
    return stats

    def get_referral_stats_by_type(self, user_id, deposit_type):
    """Получить статистику рефералов по типу депозита (только с активными вкладами)"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Получаем количество рефералов по уровням с активными вкладами
        # определенного типа
        cursor.execute('''
    SELECT
    r.level,
    COUNT(*) as count
    FROM referral_relations r
    JOIN users u ON r.referred_id = u.telegram_id
    WHERE r.referrer_id = ?
    AND (
    (u.active_deposits_10 > 0 AND ? = '10_days') OR
    (u.active_deposits_30 > 0 AND ? = '30_days')
    )
    GROUP BY r.level
        ''', (user_id, deposit_type, deposit_type))

        results = cursor.fetchall()

        # Создаем словарь с результатами (только 3 уровня)
        stats = {
            'level_1': 0, 'level_2': 0, 'level_3': 0,
            'total': 0
        }

        for level, count in results:
    if 1 <= level <= 3:
    stats[f'level_{level}'] = count
    stats['total'] += count

    return stats

    def get_user_by_referral_code(self, referral_code):
    """Получить пользователя по реферальному коду"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE referral_code = ?', (referral_code,))
        user = cursor.fetchone()
        if user:
    return {
        'telegram_id': user[0],
        'username': user[1],
        'first_name': user[2],
        'last_name': user[3],
        'referral_code': user[4],
        'referred_by': user[5],
        'balance': user[6]
    }
    return None

    def set_referred_by(self, telegram_id, referral_code):
    """Установить реферала (только регистрация по ссылке)"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        referrer = cursor.execute(
            'SELECT telegram_id FROM users WHERE referral_code = ?',
            (referral_code,
             )).fetchone()
        if not referrer:
    return False
    referrer_id = referrer[0]
    cursor.execute(
        'UPDATE users SET referred_by = ? WHERE telegram_id = ?',
        (referral_code,
         telegram_id))

    # Записываем регистрацию по ссылке
    cursor.execute('''
    INSERT INTO referral_registrations (referrer_id, referred_id)
    VALUES (?, ?)
        ''', (referrer_id, telegram_id))

    conn.commit()
    return True

    def create_referral_relations_on_payment(self, referred_id: int):
    """Создать реферальные связи при пополнении"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Получаем реферера
        user = cursor.execute(
            'SELECT referred_by FROM users WHERE telegram_id = ?',
            (referred_id,
             )).fetchone()
        if not user or not user[0]:
    return

    referrer_code = user[0]
    referrer = cursor.execute(
        'SELECT telegram_id FROM users WHERE referral_code = ?',
        (referrer_code,
         )).fetchone()
    if not referrer:
    return

    referrer_id = referrer[0]

    # Создаем многоуровневые связи
    self._create_referral_relations(
        cursor, referrer_id, referred_id, 1)
    conn.commit()

    def _create_referral_relations(
            self,
            cursor,
            referrer_id: int,
            referred_id: int,
            level: int):
    """Создать реферальные связи для всех уровней"""
    if level > 6:  # MAX_REFERRAL_LEVEL
        return
        cursor.execute(
            'INSERT INTO referral_relations (referrer_id, referred_id, level) VALUES (?, ?, ?)',
            (referrer_id,
             referred_id,
             level))
    parent_referrer = cursor.execute(
        'SELECT referred_by FROM users WHERE telegram_id = ?',
        (referrer_id,
         )).fetchone()
    if parent_referrer and parent_referrer[0]:
        parent_id = cursor.execute(
            'SELECT telegram_id FROM users WHERE referral_code = ?',
            (parent_referrer[0],
             )).fetchone()
        if parent_id:
        self._create_referral_relations(
            cursor, parent_id[0], referred_id, level + 1)

        def get_registrations_count(self, telegram_id):
    """Получить количество регистраций по ссылке"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        count = cursor.execute('''
    SELECT COUNT(*) FROM referral_registrations
    WHERE referrer_id = ?
        ''', (telegram_id,)).fetchone()[0] or 0

        return count

        def get_total_referral_earned(self, telegram_id):
    """Получить общий доход с рефералов"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Получаем total_earned из таблицы users
        total_earned = cursor.execute('''
    SELECT COALESCE(total_earned, 0) FROM users
    WHERE telegram_id = ?
        ''', (telegram_id,)).fetchone()[0] or 0

        return total_earned

        def get_total_referral_earned_by_type(self, user_id, deposit_type):
    """Получить доход с рефералов по типу депозита"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Пока что возвращаем 0, так как нужно будет реализовать расчет
        # на основе транзакций с учетом типа депозита
        return 0.0

        def is_admin(self, telegram_id):
    """Проверить, является ли пользователь администратором"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        admin = cursor.execute(
            'SELECT telegram_id FROM admins WHERE telegram_id = ?',
            (telegram_id,
             )).fetchone()
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

        def create_withdrawal_request(self, user_id, amount, wallet_address):
    """Создать заявку на вывод"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
    INSERT INTO withdrawal_requests (user_id, amount, wallet_address)
    VALUES (?, ?, ?)
        ''', (user_id, amount, wallet_address))
        conn.commit()
        return cursor.lastrowid

        def get_withdrawal_requests(self, status='pending'):
    """Получить заявки на вывод"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        requests = cursor.execute('''
    SELECT wr.*, u.username, u.first_name, u.last_name
    FROM withdrawal_requests wr
    LEFT JOIN users u ON wr.user_id = u.telegram_id
    WHERE wr.status = ?
    ORDER BY wr.created_at DESC
        ''', (status,)).fetchall()

        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, request)) for request in requests]

        def update_withdrawal_status(self, request_id, status, admin_id):
    """Обновить статус заявки на вывод"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
    UPDATE withdrawal_requests
    SET status = ?, admin_id = ?, processed_at = CURRENT_TIMESTAMP
    WHERE id = ?
        ''', (status, admin_id, request_id))
        conn.commit()

        def get_bot_statistics(self):
    """Получить статистику бота"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Общее количество пользователей
        total_users = cursor.execute(
            'SELECT COUNT(*) FROM users').fetchone()[0]

        # Общий баланс всех пользователей
        total_balance = cursor.execute(
            'SELECT COALESCE(SUM(balance), 0) FROM users').fetchone()[0] or 0

        # Общий доход от рефералов
        total_referral_earned = cursor.execute(
            'SELECT COALESCE(SUM(amount), 0) FROM referral_payments').fetchone()[0] or 0

        # Количество заявок на вывод
        pending_withdrawals = cursor.execute(
            'SELECT COUNT(*) FROM withdrawal_requests WHERE status = "pending"').fetchone()[0]

        return {
            'total_users': total_users,
            'total_balance': total_balance,
            'total_referral_earned': total_referral_earned,
            'pending_withdrawals': pending_withdrawals
        }

        def get_daily_deposits_stats(self):
    """Получить статистику поступлений за последние 10 дней"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Получаем статистику по дням за последние 10 дней
        cursor.execute('''
    SELECT
    DATE(created_at) as deposit_date,
    COUNT(*) as deposits_count,
    SUM(amount) as total_amount,
    SUM(CASE WHEN deposit_type = '10_days' THEN amount ELSE 0 END) as amount_10_days,
    SUM(CASE WHEN deposit_type = '30_days' THEN amount ELSE 0 END) as amount_30_days
    FROM user_transactions
    WHERE status = 'success'
    AND created_at >= date('now', '-10 days')
    GROUP BY DATE(created_at)
    ORDER BY deposit_date DESC
        ''')

        daily_stats = cursor.fetchall()

        # Общая статистика за 10 дней
        cursor.execute('''
    SELECT
    COUNT(*) as total_deposits,
    SUM(amount) as total_amount,
    SUM(CASE WHEN deposit_type = '10_days' THEN amount ELSE 0 END) as total_10_days,
    SUM(CASE WHEN deposit_type = '30_days' THEN amount ELSE 0 END) as total_30_days
    FROM user_transactions
    WHERE status = 'success'
    AND created_at >= date('now', '-10 days')
        ''')

        total_stats = cursor.fetchone()

        return {
            'daily_stats': daily_stats,
            'total_stats': total_stats
        }

        async def safe_edit_message(
                self,
                update: Update,
                text: str,
                reply_markup=None,
                parse_mode='HTML'):
    """Безопасное редактирование сообщения - всегда заменяем существующее"""
    try:
        # Сначала пытаемся отредактировать caption (если есть фото)
        if update.callback_query.message.photo:
    await update.callback_query.edit_message_caption(
        caption=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )
    else:
        # Если нет фото, редактируем текст
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )
    except Exception as e:
        # Если не удалось отредактировать, удаляем старое сообщение и
        # отправляем новое
        try:
    await update.callback_query.message.delete()
    except BaseException:
    pass
    await update.callback_query.message.reply_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )

    async def cleanup_messages(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Очистка предыдущих сообщений, кроме команды /start"""
    try:
        chat_id = update.effective_chat.id
        current_message_id = update.effective_message.message_id

    logger.info(
        f"🧹 Очистка сообщений для чата {chat_id}, текущее сообщение: {current_message_id}")

    # Проверяем, не является ли текущее сообщение командой /start
    if update.effective_message and update.effective_message.text:
    if update.effective_message.text.startswith('/start'):
        # Сохраняем ID сообщения с командой /start
        self.save_start_message_id(chat_id, current_message_id)
        # Не удаляем сообщения, если это команда /start
    return

    # Получаем ID сообщения с командой /start для этого чата
    start_message_id = self.start_message_ids.get(chat_id, 0)
    logger.info(
        f"📍 ID сообщения /start для чата {chat_id}: {start_message_id}")

    # Если ID сообщения /start не найден, не удаляем ничего
    if start_message_id == 0:
    logger.warning(
        f"⚠️ ID сообщения /start не найден для чата {chat_id}, пропускаем очистку")
    return

    # Удаляем предыдущие сообщения (кроме команды /start)
    deleted_count = 0
    for i in range(max(1, current_message_id - 5), current_message_id):
        # Не удаляем сообщение с командой /start
    if i == start_message_id:
    logger.info(
        f"⏭️ Пропускаем удаление сообщения /start: {i}")
    continue
    try:
    await context.bot.delete_message(chat_id, i)
    deleted_count += 1
    logger.info(f"🗑️ Удалено сообщение {i} из чата {chat_id}")
    except Exception as e:
        # Игнорируем ошибки удаления (сообщение может не существовать)
    logger.debug(f"Не удалось удалить сообщение {i}: {e}")
    pass

    logger.info(f"✅ Очистка завершена. Удалено сообщений: {deleted_count}")

    except Exception as e:
        logger.error(f"Ошибка очистки сообщений: {e}")

        async def start_command(
                self,
                update: Update,
                context: ContextTypes.DEFAULT_TYPE):
    """Быстрый старт"""
    user = update.effective_user

    # Сохраняем ID сообщения с командой /start
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    self.save_start_message_id(chat_id, message_id)

    # Не очищаем сообщения для команды /start, чтобы кнопка "Начать" не
    # исчезала

    # Быстро создаем пользователя
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

        # Показываем меню
    await self.show_main_menu(update, context)

    async def menu_command(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Быстрое меню"""
    await self.show_main_menu(update, context)

    async def add_admin_command(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Команда для добавления администратора"""
    user = update.effective_user

    # Проверяем, является ли пользователь администратором
    if not self.is_admin(user.id):
        await update.message.reply_text("❌ У вас нет прав для добавления администраторов")
        return

    if not context.args:
        await update.message.reply_text("Использование: /addadmin @username")
        return

        # Получаем username из аргументов
    username = context.args[0].replace('@', '')

    # Здесь нужно найти пользователя по username и добавить его как администратора
    # Для простоты, будем добавлять по telegram_id
    try:
        admin_id = int(username)  # Предполагаем, что передается ID
        self.add_admin(admin_id, f"admin_{admin_id}", "Admin", "User")
        await update.message.reply_text(f"✅ Пользователь {admin_id} добавлен как администратор")
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Используйте: /addadmin <telegram_id>")

        async def show_main_menu(
                self,
                update: Update,
                context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню"""
    user = update.effective_user

    # Проверяем, является ли пользователь администратором
    is_admin = self.is_admin(user.id)

    keyboard = [
        [InlineKeyboardButton("💰 Внести средства", callback_data="deposit")],
        [InlineKeyboardButton("👥 Реферальная система", callback_data="referrals")],
        [InlineKeyboardButton("📊 Ваши вклады", callback_data="transactions")],
        [InlineKeyboardButton("ℹ️ Информация", callback_data="info")]
    ]

    # Добавляем админские кнопки
    if is_admin:
        keyboard.append([InlineKeyboardButton(
            "🔧 Админ панель", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = """
ФондКлик — это платформа для управления цифровыми активами, где пользователи могут размещать краткосрочные депозиты с фиксированной доходностью.

Пул из размещенных вкладов используется в работе нескольких проектов, прибыль от которых распределяется между пользователями, предоставившими свои средства.

Выберите действие:
    """

    # File ID для прямоугольного логотипа
    logo_file_id = "AgACAgIAAxkBAAIBDmjim1zNk93yL6_tUBCBY25YMiJEAAIhCzIbE78ZS41rgE0b6voHAQADAgADeQADNgQ"

    if update.callback_query:
        # Для навигации всегда заменяем сообщение
        try:
            # Сначала пытаемся отредактировать caption (если есть фото)
    if update.callback_query.message.photo:
    await update.callback_query.edit_message_caption(
        caption=message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    else:
        # Если нет фото, удаляем старое сообщение и отправляем новое с фото
    try:
    await update.callback_query.message.delete()
    except BaseException:
    pass
    await update.callback_query.message.reply_photo(
        photo=logo_file_id,
        caption=message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    except Exception as e:
        # Если не удалось отредактировать, удаляем старое и отправляем новое
        # фото
    try:
    await update.callback_query.message.delete()
    except BaseException:
    pass
    await update.callback_query.message.reply_photo(
        photo=logo_file_id,
        caption=message_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    else:
        # Для нового сообщения всегда отправляем фото
        await update.message.reply_photo(
            photo=logo_file_id,
            caption=message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

        async def button_callback(
                self,
                update: Update,
                context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()

    # Очищаем предыдущие сообщения при навигации (кроме команды /start)
    # Расширенный список кнопок для очистки
    cleanup_buttons = [
        "back_to_menu",
        "deposit",
        "referrals",
        "transactions",
        "info",
        "deposit_30_days",
        "deposit_10_days",
        "deposit_7_days",
        "deposit_3_days",
        "check_any_amount_",
        "wallet_info",
        "check_payment_",
        "check_"]

    # Проверяем, нужно ли очищать сообщения
    should_cleanup = False
    for button in cleanup_buttons:
        if query.data.startswith(button) or query.data == button:
    should_cleanup = True
    break

    if should_cleanup:
        await self.cleanup_messages(update, context)

    data = query.data

    if data == "deposit":
        await self.show_deposit_menu(update, context)
    elif data == "deposit_30_days":
        context.user_data['deposit_type'] = '30_days'
        await self.enter_wallet(update, context)
    elif data == "deposit_10_days":
        context.user_data['deposit_type'] = '10_days'
        await self.enter_wallet(update, context)
    elif data == "enter_wallet":
        await self.enter_wallet(update, context)
    elif data == "referrals":
        await self.show_referrals(update, context)
    elif data == "transactions":
        await self.show_user_transactions(update, context)
    elif data == "info":
        await self.show_info(update, context)
    elif data == "admin_panel":
        await self.show_admin_panel(update, context)
    elif data == "withdrawal":
        await self.show_withdrawal_menu(update, context)
    elif data == "withdrawal_requests":
        await self.show_withdrawal_requests(update, context)
    elif data == "deposit_payments":
    logger.info("Обработка кнопки deposit_payments")
    await self.show_deposit_payments(update, context)
    elif data == "completed_payments":
    logger.info("Обработка кнопки completed_payments")
    await self.show_completed_payments(update, context)
    elif data == "bot_statistics":
        await self.show_bot_statistics(update, context)
    elif data == "daily_deposits_stats":
        await self.show_daily_deposits_stats(update, context)
    elif data == "help":
        await self.show_help(update, context)
    elif data == "back_to_menu":
        await self.show_main_menu(update, context)
    elif data.startswith("amount_"):
        amount = data.split("_")[1]
        await self.process_deposit_amount(update, context, amount)
    elif data == "custom_amount":
        await self.enter_custom_amount(update, context)
    elif data.startswith("check_usdt_"):
        # Обработка проверки USDT платежа
        parts = data.split("_")
        user_id = int(parts[2])
        amount = float(parts[3])
        await self.check_usdt_payment_callback(update, context, user_id, amount)
    elif data.startswith("check_any_amount_"):
        # Обработка проверки платежа с любой суммой
        user_id = int(data.split("_")[3])
        await self.check_any_amount_payment_callback(update, context, user_id)
    elif data.startswith("approve_"):
        request_id = data.split("_")[1]
        await self.approve_withdrawal(update, context, request_id)
    elif data.startswith("pay_deposit_"):
        payment_id = data.split("_")[2]
        await self.pay_deposit(update, context, payment_id)

        async def show_deposit_menu(
                self,
                update: Update,
                context: ContextTypes.DEFAULT_TYPE):
    """Показать меню пополнения"""
    keyboard = [
        [
            InlineKeyboardButton(
                "📅 Внести на 30 дней (30% прибыль)", callback_data="deposit_30_days")], [
            InlineKeyboardButton(
                "📅 Внести на 10 дней (8% прибыль)", callback_data="deposit_10_days")], [
            InlineKeyboardButton(
                "🔙 Назад в меню", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = """
💰 ВНЕСЕНИЕ СРЕДСТВ

Выберите тип депозита:
    """

    await self.safe_edit_message(update, message_text, reply_markup)

    async def show_transactions(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Показать транзакции"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = """
📊 МОИ ТРАНЗАКЦИИ

У вас пока нет транзакций.

Для пополнения баланса обратитесь к администратору.
    """

    await self.safe_edit_message(update, message_text, reply_markup)

    async def show_user_transactions(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Показать вклады пользователя"""
    user_id = update.effective_user.id

    try:
    logger.info(f"Показываем вклады для пользователя {user_id}")

    # Получаем активные вклады
    active_deposits = self.get_user_active_deposits(user_id)
    logger.info(
        f"Активных вкладов: {
            len(active_deposits) if active_deposits else 0}")

    # Получаем историю выплаченных вкладов
    paid_deposits = self.get_user_paid_deposits(user_id)
    logger.info(
        f"Выплаченных вкладов: {
            len(paid_deposits) if paid_deposits else 0}")
    except Exception as e:
        logger.error(
            f"Ошибка при получении вкладов для пользователя {user_id}: {e}")
        await self.safe_edit_message(
            update,
            "❌ Ошибка при загрузке вкладов. Попробуйте позже.",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]])
        )
        return

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
        message_text += f"... и еще {len(paid_deposits) -
                                     5} выплаченных депозитов\n"
    else:
        message_text += "\n📜 ИСТОРИЯ ВЫПЛАЧЕННЫХ ВКЛАДОВ:\nНет выплаченных вкладов\n"

    keyboard = [
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await self.safe_edit_message(update, message_text, reply_markup, 'HTML')
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

        def create_user_transaction(
                self,
                user_id,
                amount,
                deposit_type,
                wallet_address,
                invoice_id):
    """Создать запись транзакции пользователя"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Устанавливаем время истечения через час
        expires_at = datetime.now() + timedelta(hours=1)

        cursor.execute('''
    INSERT INTO user_transactions
    (user_id, amount, deposit_type, status, wallet_address, invoice_id, expires_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, deposit_type, 'pending', wallet_address, invoice_id, expires_at))

        conn.commit()
        return cursor.lastrowid

        def get_user_active_deposits(self, user_id):
    """Получить активные вклады пользователя"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute('''
    SELECT dp.original_amount, dp.deposit_type, dp.days_remaining, dp.created_at
    FROM deposit_payments dp
    WHERE dp.user_id = ? AND dp.status = 'pending'
    ORDER BY dp.created_at DESC
        ''', (user_id,))

        return cursor.fetchall()

        def get_user_paid_deposits(self, user_id):
    """Получить выплаченные вклады пользователя"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute('''
    SELECT dp.original_amount, dp.deposit_type, dp.payment_date, dp.return_amount
    FROM deposit_payments dp
    WHERE dp.user_id = ? AND dp.status = 'paid'
    ORDER BY dp.payment_date DESC
        ''', (user_id,))

        return cursor.fetchall()

        def get_user_active_deposits_count(self, user_id):
    """Получить количество активных депозитов пользователя"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
    SELECT COUNT(*) FROM deposit_payments
    WHERE user_id = ? AND status = 'pending'
        ''', (user_id,))
        return cursor.fetchone()[0]

        def get_user_successful_transactions(self, user_id):
    """Получить успешные транзакции пользователя"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute('''
    SELECT id, amount, deposit_type, status, wallet_address, created_at
    FROM user_transactions
    WHERE user_id = ? AND status = 'success'
    ORDER BY created_at DESC
        ''', (user_id,))

        return cursor.fetchall()

        def cleanup_expired_transactions(self):
    """Удалить истекшие транзакции"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Удаляем транзакции, которые истекли и не были успешными
        cursor.execute('''
    DELETE FROM user_transactions
    WHERE expires_at < ? AND status != 'success'
        ''', (datetime.now(),))

        conn.commit()
        return cursor.rowcount

        async def check_pending_payments(self):
    """Проверить статус ожидающих платежей"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Получаем все ожидающие транзакции
        cursor.execute('''
    SELECT id, user_id, amount, deposit_type, invoice_id
    FROM user_transactions
    WHERE status = 'pending' AND expires_at > ?
        ''', (datetime.now(),))

        pending_transactions = cursor.fetchall()

        for transaction in pending_transactions:
    trans_id, user_id, amount, deposit_type, invoice_id = transaction

    # Получаем кошелек пользователя из транзакции
    cursor.execute(
        'SELECT wallet_address FROM user_transactions WHERE id = ?', (trans_id,))
    wallet_result = cursor.fetchone()

    if wallet_result:
    user_wallet = wallet_result[0]

    # Проверяем USDT платеж
    result = await self.check_usdt_payment(user_wallet, amount)

    if result["status"] == "paid":
        # Платеж успешен
        self.process_payment_success(
            user_id, result["amount"], deposit_type, trans_id)
    logger.info(
        f"✅ USDT платеж {trans_id} успешно обработан: {
            result['amount']} USDT")
    elif result["status"] == "error":
        # Ошибка проверки
        cursor.execute(
            'UPDATE user_transactions SET status = ? WHERE id = ?',
            ('failed',
             trans_id))
    logger.info(
        f"❌ USDT платеж {trans_id} отменен (ошибка: {
            result['message']})")
    else:
    logger.warning(f"Не найден кошелек для транзакции {trans_id}")

    conn.commit()

    async def show_info(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о боте"""
    message_text = """
ℹ️ ИНФОРМАЦИЯ

📊 РЕФЕРАЛЬНАЯ СИСТЕМА

Наша реферальная система построена на принципе многоуровневого партнерства:

🔗 Как работает 3-уровневая система:
• Вы получаете уникальную реферальную ссылку
• Приглашаете людей через эту ссылку
• Когда приглашенный человек делает депозит, вы получаете вознаграждение
• Система работает на 3 уровня вглубь

💰 Размер вознаграждений по уровням:
• 1-й уровень: 15% (30 дней) / 5% (10 дней)
• 2-й уровень: 10% (30 дней) / 3% (10 дней)
• 3-й уровень: 5% (30 дней) / 1.5% (10 дней)

💡 Как работает система уровней:
• 1-й уровень: люди, которых пригласили вы напрямую
• 2-й уровень: люди, которых пригласили ваши рефералы
• 3-й уровень: люди, которых пригласили рефералы 2-го уровня

💡 Важные особенности:
• Вознаграждения начисляются только с активных депозитов
• Если у человека истекает депозит, он исчезает из вашей реферальной сети
• При новом депозите он снова появляется в системе
• Чем больше людей вы пригласите, тем больше заработаете

📈 ТИПЫ ДЕПОЗИТОВ

💰 10-дневные депозиты:
• Доходность: 8% от суммы
• Срок: 10 дней
• Минимальная сумма: 50 USDT

💰 30-дневные депозиты:
• Доходность: 30% от суммы
• Срок: 30 дней
• Минимальная сумма: 50 USDT

⚖️ ПРАВОВАЯ ИНФОРМАЦИЯ

ВНИМАНИЕ: Данная платформа предоставляет исключительно информационные услуги и не является финансовым учреждением, банком или инвестиционной компанией.

🔸 Все операции осуществляются на добровольной основе
🔸 Пользователи несут полную ответственность за свои решения
🔸 Платформа не гарантирует доходность и не несет ответственности за возможные убытки
🔸 Все средства передаются в качестве подарка/благодарности
🔸 Пользователь подтверждает, что понимает риски и действует на свой страх и риск
    """

    keyboard = [
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await self.safe_edit_message(update, message_text, reply_markup, 'HTML')
    else:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

        async def show_referrals(
                self,
                update: Update,
                context: ContextTypes.DEFAULT_TYPE):
    """Показать рефералов"""
    user = update.effective_user

    # Получаем статистику рефералов с активными вкладами
    referral_stats_10 = self.get_referral_stats_by_type(user.id, '10_days')
    referral_stats_30 = self.get_referral_stats_by_type(user.id, '30_days')

    # Получаем общий доход от рефералов
    total_earned_10 = self.get_total_referral_earned_by_type(
        user.id, '10_days')
    total_earned_30 = self.get_total_referral_earned_by_type(
        user.id, '30_days')

    # Получаем количество регистраций по ссылке
    registrations_count = self.get_registrations_count(user.id)

    # Получаем реферальный код
    user_data = self.get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    referral_link = f"https://t.me/{
        context.bot.username}?start={
        user_data['referral_code']}"

    keyboard = [
        [InlineKeyboardButton("💸 Вывод средств", callback_data="withdrawal")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = f"""
👥 РЕФЕРАЛЬНАЯ СИСТЕМА

🔗 Ваша ссылка: `{referral_link}`

📊 РЕФЕРАЛЫ ПО УРОВНЯМ (С АКТУАЛЬНЫМИ ВКЛАДАМИ):

📅 На 30 дней (15% / 10% / 5%):
1-й: {referral_stats_30['level_1']}
2-й: {referral_stats_30['level_2']}
3-й: {referral_stats_30['level_3']}

📅 На 10 дней (5% / 3% / 1.5%):
1-й: {referral_stats_10['level_1']}
2-й: {referral_stats_10['level_2']}
3-й: {referral_stats_10['level_3']}

💵 Общий доход: {total_earned_30 + total_earned_10:.2f} USDT

👤 Зарегистрировано по моей ссылке: {registrations_count} чел.

💡 Приглашайте по ссылке → получайте % с пополнений до 3 уровня
    """

    await self.safe_edit_message(update, message_text, reply_markup, 'Markdown')

    async def show_help(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Показать помощь"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = """
ℹ️ ПОМОЩЬ

🔺 Пирамммида - это бот для работы с USDT

Основные функции:
• Пополнение баланса
• Реферальная программа
• Быстрые переводы

Для получения помощи обратитесь к администратору.
    """

    await self.safe_edit_message(update, message_text, reply_markup)

    async def enter_wallet(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Запрос USDT адреса"""
    context.user_data['waiting_for_wallet'] = True

    # Получаем тип депозита
    deposit_type = context.user_data.get('deposit_type', '10_days')

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="deposit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if deposit_type == '30_days':
        message_text = """
💳 ВВОД USDT АДРЕСА

📅 Тип депозита: 30 дней (30% прибыль)

Введите ваш USDT кошелек (TRC20):

⚠️ ВАЖНО:
• Деньги будут выплачиваться ТОЛЬКО на указанный кошелек изменить его будет невозможно
• Совершайте внесение средств на депозит с этого же кошелька
• Убедитесь, что адрес указан правильно
    """
    else:
        message_text = """
💳 ВВОД USDT АДРЕСА

📅 Тип депозита: 10 дней (8% прибыль)

Введите ваш USDT кошелек (TRC20):

⚠️ ВАЖНО:
• Деньги будут выплачиваться ТОЛЬКО на указанный кошелек изменить его будет невозможно
• Совершайте внесение средств на депозит с этого же кошелька
• Убедитесь, что адрес указан правильно
    """

    await self.safe_edit_message(update, message_text, reply_markup)

    async def show_payment_instructions(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            wallet_address: str):
    """Показать инструкции по оплате без выбора суммы"""
    try:
        user_id = update.effective_user.id
        deposit_type = context.user_data.get('deposit_type', '10_days')

        # Получаем информацию о кошельке для оплаты
        wallet_info = self.payment_client.get_wallet_info()

        if not wallet_info.get("success"):
    await update.message.reply_text(
        "❌ Ошибка получения информации о кошельке для оплаты.\n\nПопробуйте позже или обратитесь в поддержку."
    )
    return

    payment_wallet = wallet_info["wallet_address"]

    # Создаем уникальный ID для отслеживания
    tracking_id = f"usdt_{user_id}_{int(datetime.now().timestamp())}"

    # Регистрируем ожидаемый платеж в системе бота
    self.pending_payments[wallet_address] = {
        'user_id': user_id,
        'deposit_type': deposit_type,
        'tracking_id': tracking_id,
        'payment_wallet': payment_wallet
    }

    # Сохраняем данные для отслеживания в контексте пользователя
    context.user_data['payment_tracking'] = {
        'user_wallet': wallet_address,
        'payment_wallet': payment_wallet,
        'deposit_type': deposit_type,
        'tracking_id': tracking_id,
        'user_id': user_id
    }

    logger.info(
        f"Зарегистрирован ожидаемый платеж от {wallet_address} для пользователя {user_id}")

    keyboard = [
        [InlineKeyboardButton("✅ Проверить платеж", callback_data=f"check_any_amount_{user_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="deposit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Форматируем тип вклада для отображения
    deposit_display = deposit_type.replace('_', ' ').title()
    if deposit_type == '30_days':
    deposit_display = "30 Days"
    elif deposit_type == '10_days':
    deposit_display = "10 Days"
    elif deposit_type == '7_days':
    deposit_display = "7 Days"
    elif deposit_type == '3_days':
    deposit_display = "3 Days"

    message_text = f"""
💰 ВНЕСЕНИЕ ВКЛАДА

📋 Инструкция по оплате:
1️⃣ переведите любую сумму которую вы хотите внести на «кошелек для оплаты» (указан ниже)
2️⃣ Для осуществления перевода используйте ваш кошелек который вы указали ранее (указан ниже)
3️⃣ Нажмите "✅ Проверить платеж" после отправки

🏦 Кошелек для оплаты:
{payment_wallet}

👤 Ваш кошелек (отправитель):
{wallet_address}

📅 Тип вклада: {deposit_display}
🆔 ID отслеживания: {tracking_id}

💡 Вы можете отправить любую сумму от 50 USDT
⚠️ ВАЖНО:
• Используйте для внесения депозита ранее указанный вами кошелек
• Система автоматически определит и зачислит полученную сумму
        """

    await update.message.reply_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

    except Exception as e:
        logger.error(f"Ошибка показа инструкций по оплате: {e}")
        await update.message.reply_text(
            "❌ Ошибка отображения инструкций. Попробуйте позже."
        )

        async def enter_custom_amount(
                self,
                update: Update,
                context: ContextTypes.DEFAULT_TYPE):
    """Запрос произвольной суммы"""
    context.user_data['waiting_for_custom_amount'] = True

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="enter_wallet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = """
💳 ВВОД СУММЫ

Введите сумму депозита в USDT:
💡 Минимальная сумма: 50 USDT
    """

    await self.safe_edit_message(update, message_text, reply_markup)

    async def process_deposit_amount(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            amount: str):
    """Обработка выбора суммы"""
    try:
        amount_float = float(amount)

        # Проверяем минимальную сумму
        if amount_float < 50:
    await self.safe_edit_message(
        update,
        "❌ Минимальная сумма депозита: 50 USDT",
        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="enter_wallet")]])
    )
    return

    user_id = update.effective_user.id

    # Проверяем количество активных вкладов
    active_deposits_count = self.get_user_active_deposits_count(user_id)
    if active_deposits_count >= 10:
    await self.safe_edit_message(
        update,
        f"❌ У вас уже есть {active_deposits_count} активных вкладов\n\n"
        "Максимальное количество активных вкладов: 10\n"
        "Дождитесь выплаты одного из вкладов, чтобы создать новый.",
        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]])
    )
    return

    # Получаем кошелек пользователя
    wallet_address = context.user_data.get('wallet_address', '')
    deposit_type = context.user_data.get('deposit_type', '10_days')

    # Создаем запрос на USDT платеж
    logger.info(
        f"Создаем запрос на USDT платеж для пользователя {user_id} на сумму {amount_float}")
    payment_data = await self.create_payment_request(amount_float, user_id, wallet_address)
    logger.info(f"Результат создания запроса на платеж: {payment_data}")

    if payment_data:

        # Создаем запись транзакции
    transaction_id = self.create_user_transaction(
        user_id=user_id,
        amount=amount_float,
        deposit_type=deposit_type,
        wallet_address=wallet_address,
        invoice_id=f"usdt_{user_id}_{int(datetime.now().timestamp())}"
    )

    context.user_data['pending_payment'] = {
        'amount': amount_float,
        'user_id': user_id,
        'user_wallet': wallet_address,
        'payment_wallet': payment_data['payment_wallet'],
        'deposit_type': deposit_type,
        'transaction_id': transaction_id
    }

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Проверить оплату", callback_data=f"check_usdt_{user_id}_{amount_float}")], [
            InlineKeyboardButton(
                "🔙 Назад", callback_data="deposit")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = f"""
💰 ВНЕСЕНИЕ ВКЛАДА

📋 Инструкция по оплате:
1️⃣ Отправьте {amount_float} USDT на указанный кошелек
2️⃣ Используйте ваш кошелек как отправитель
3️⃣ Нажмите "✅ Проверить оплату" после отправки

🏦 Кошелек для оплаты:
`{payment_data['payment_wallet']}`

👤 Ваш кошелек (отправитель):
`{wallet_address}`

💰 Сумма к оплате: {amount_float} USDT
📅 Тип вклада: {deposit_type.replace('_', ' ').title()}
🆔 ID транзакции: {transaction_id}

⚠️ ВАЖНО: Отправляйте точную сумму {amount_float} USDT!
    """

    await self.safe_edit_message(update, message_text, reply_markup)
    else:
    logger.error(
        f"Не удалось получить информацию о кошельке для пользователя {user_id}")
    await self.safe_edit_message(
        update,
        "❌ Ошибка получения информации о кошельке для оплаты.\n\nПопробуйте позже или обратитесь в поддержку.",
        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="deposit")]])
    )

    except Exception as e:
        logger.error(f"Ошибка обработки суммы: {e}")
        await self.safe_edit_message(
            update,
            "❌ Ошибка. Попробуйте позже.",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="deposit")]])
        )

        def process_payment_success(
                self,
                user_id: int,
                amount: float,
                deposit_type: str = '10_days',
                transaction_id: int = None):
    """Обработать успешный платеж"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Обновляем баланс пользователя
        cursor.execute(
            'UPDATE users SET balance = balance + ? WHERE telegram_id = ?',
            (amount,
             user_id))

        # Обновляем счетчики активных депозитов
        if deposit_type == '10_days':
        cursor.execute(
            'UPDATE users SET active_deposits_10 = active_deposits_10 + 1 WHERE telegram_id = ?',
            (user_id,
             ))
        else:
        cursor.execute(
            'UPDATE users SET active_deposits_30 = active_deposits_30 + 1 WHERE telegram_id = ?',
            (user_id,
             ))

        # Обновляем статус транзакции на успешную
        if transaction_id:
        cursor.execute(
            'UPDATE user_transactions SET status = ? WHERE id = ?',
            ('success',
             transaction_id))

        # Создаем реферальные связи при первом пополнении
        self.create_referral_relations_on_payment(user_id)

        # Создаем расписание выплат вклада
        self.create_deposit_payment_schedule(user_id, amount, deposit_type)

        conn.commit()

        def create_deposit_payment_schedule(
                self, user_id, amount, deposit_type='10_days'):
    """Создать расписание выплат вклада"""
    from datetime import datetime, timedelta

    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Получаем адрес кошелька пользователя
        cursor.execute(
            'SELECT wallet_address FROM users WHERE telegram_id = ?', (user_id,))
        wallet_result = cursor.fetchone()
        wallet_address = wallet_result[0] if wallet_result and wallet_result[0] else "Не указан"

        # Определяем параметры в зависимости от типа депозита
        if deposit_type == '30_days':
    total_days = 30
    profit_percent = 0.30  # 30% прибыль
    else:  # 10_days
    total_days = 10
    profit_percent = 0.08  # 8% прибыль

    # Рассчитываем сумму к возврату
    return_amount = amount * (1 + profit_percent)

    # Создаем записи для каждого дня
    for days_remaining in range(total_days, 0, -1):
    payment_date = datetime.now() + timedelta(days=days_remaining - 1)

    cursor.execute('''
    INSERT INTO deposit_payments
    (user_id, original_amount, return_amount, payment_date, days_remaining, status, wallet_address, deposit_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, amount, return_amount, payment_date.strftime('%Y-%m-%d'), days_remaining, 'pending', wallet_address, deposit_type))

    conn.commit()
    logger.info(
        f"Создано расписание выплат для пользователя {user_id}: {amount} USDT -> {
            return_amount:.2f} USDT за {total_days} дней ({deposit_type}), кошелек: {wallet_address}")

    def get_deposit_payments_by_day(self, deposit_type=None):
    """Получить выплаты вкладов сгруппированные по дням"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()

    # Базовый запрос
    base_query = '''
    WITH numbered_payments AS (
    SELECT
    dp.days_remaining,
    dp.payment_date,
    dp.id,
    dp.wallet_address,
    dp.return_amount,
    dp.deposit_type,
    ROW_NUMBER() OVER (PARTITION BY dp.days_remaining, dp.deposit_type ORDER BY dp.id) as day_number
    FROM deposit_payments dp
    WHERE dp.status = 'pending'
    '''

    # Добавляем фильтр по типу депозита если указан
    if deposit_type:
    base_query += f" AND dp.deposit_type = '{deposit_type}'"

    base_query += '''
    )
    SELECT
    days_remaining,
    payment_date,
    deposit_type,
    COUNT(*) as payment_count,
    SUM(return_amount) as total_amount,
    GROUP_CONCAT(
    '#' || day_number || '. ' ||
    COALESCE(wallet_address, 'Не указан') || ' - ' ||
    return_amount || ' USDT - ' || payment_date || ' (' || deposit_type || ')',
    '\n'
    ) as payment_details
    FROM numbered_payments
    GROUP BY days_remaining, payment_date, deposit_type
    ORDER BY days_remaining DESC
    '''

    cursor.execute(base_query)
    results = cursor.fetchall()
    return results
    except Exception as e:
        logger.error(f"Ошибка в get_deposit_payments_by_day: {e}")
        return []

        def get_first_deposit_payment_for_day(
                self, deposit_type, payment_date):
    """Получить первую заявку на выплату для конкретного дня"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()

    query = '''
    SELECT
    dp.id,
    dp.wallet_address,
    dp.return_amount as amount,
    dp.created_at,
    u.first_name,
    u.username
    FROM deposit_payments dp
    JOIN users u ON dp.user_id = u.telegram_id
    WHERE dp.deposit_type = ?
    AND dp.payment_date = ?
    AND dp.status = 'pending'
    ORDER BY dp.id
    LIMIT 1
    '''

    cursor.execute(query, (deposit_type, payment_date))
    result = cursor.fetchone()

    if result:
    return {
        'id': result[0],
        'wallet_address': result[1],
        'amount': result[2],
        'created_at': result[3],
        'first_name': result[4],
        'username': result[5]
    }
    return None
    except Exception as e:
        logger.error(f"Ошибка в get_first_deposit_payment_for_day: {e}")
        return None

        def get_first_urgent_deposit_payment(self):
    """Получить первую срочную заявку на выплату (день 1)"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()

    query = '''
    SELECT
    dp.id,
    dp.wallet_address,
    dp.return_amount as amount,
    dp.created_at,
    u.first_name,
    u.username,
    dp.deposit_type
    FROM deposit_payments dp
    JOIN users u ON dp.user_id = u.telegram_id
    WHERE dp.days_remaining = 1
    AND dp.status = 'pending'
    ORDER BY dp.id
    LIMIT 1
    '''

    cursor.execute(query)
    result = cursor.fetchone()

    if result:
    return {
        'id': result[0],
        'wallet_address': result[1],
        'amount': result[2],
        'created_at': result[3],
        'first_name': result[4],
        'username': result[5],
        'deposit_type': result[6]
    }
    return None
    except Exception as e:
        logger.error(f"Ошибка в get_first_urgent_deposit_payment: {e}")
        return None

        def get_original_amount_for_day(self, days_remaining, deposit_type):
    """Получить оригинальную сумму вложенных денег для дня"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()

    query = '''
    SELECT SUM(original_amount)
    FROM deposit_payments
    WHERE days_remaining = ?
    AND deposit_type = ?
    AND status = 'pending'
    '''

    cursor.execute(query, (days_remaining, deposit_type))
    result = cursor.fetchone()

    return result[0] if result[0] else 0
    except Exception as e:
        logger.error(f"Ошибка в get_original_amount_for_day: {e}")
        return 0

        def get_original_amount_for_payment(self, payment_id):
    """Получить оригинальную сумму вклада для конкретной заявки"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()

    query = '''
    SELECT original_amount
    FROM deposit_payments
    WHERE id = ?
    '''

    cursor.execute(query, (payment_id,))
    result = cursor.fetchone()

    return result[0] if result[0] else 0
    except Exception as e:
        logger.error(f"Ошибка в get_original_amount_for_payment: {e}")
        return 0

        async def create_payment_request(
                self,
                amount: float,
                user_id: int = None,
                user_wallet: str = None):
    """Создать запрос на USDT платеж"""
    try:
    logger.info(
        f"Создание запроса на платеж {amount} USDT для пользователя {user_id}")

    # Получаем информацию о кошельке для приема платежей
    wallet_info = self.payment_client.get_wallet_info()

    if not wallet_info.get("success"):
    logger.error(
        f"Ошибка получения информации о кошельке: {
            wallet_info.get('error')}")
    return None

    # Создаем данные для платежа
    payment_data = {
        "payment_wallet": wallet_info["wallet_address"],
        "user_wallet": user_wallet,
        "amount": amount,
        "currency": "USDT",
        "user_id": user_id,
        "wallet_balance": wallet_info.get("balance", 0)
    }

    logger.info(f"Запрос на платеж создан: {payment_data}")
    return payment_data

    except Exception as e:
        logger.error(f"Ошибка создания запроса на платеж: {e}")
        return None

        async def check_usdt_payment(
                self,
                user_wallet: str,
                expected_amount: float):
    """Проверить USDT платеж от пользователя"""
    try:
    logger.info(
        f"Проверка USDT платежа: {user_wallet} на сумму {expected_amount}")

    # Проверяем платеж через API
    result = self.payment_client.verify_payment(
        user_wallet=user_wallet,
        expected_amount=expected_amount,
        currency="USDT",
        description=f"Пополнение баланса на {expected_amount} USDT"
    )

    if result.get("success") and result.get("payment_found"):
    logger.info(f"USDT платеж подтвержден: {result['received_amount']} USDT")
    return {
        "status": "paid",
        "amount": result["received_amount"],
        "transaction_hash": result.get("transaction_hash"),
        "confirmed_at": result.get("confirmed_at")
    }
    else:
    logger.info(
        f"USDT платеж не найден: {
            result.get(
                'message',
                'Неизвестная ошибка')}")
    return {
        "status": "pending",
        "amount": 0,
        "message": result.get("message", "Платеж не найден")
    }

    except Exception as e:
        logger.error(f"Ошибка проверки USDT платежа: {e}")
        return {
            "status": "error",
            "amount": 0,
            "message": f"Ошибка проверки: {str(e)}"
        }

        async def check_any_amount_payment(self, user_wallet: str):
    """Проверить USDT платеж от пользователя с любой суммой (минимум 50 USDT)"""
    try:
    logger.info(f"Проверка USDT платежа от {user_wallet} с любой суммой")

    # Проверяем платеж через API - ищем любые поступления от этого кошелька
    result = self.payment_client.verify_payment(
        user_wallet=user_wallet,
        expected_amount=50.0,  # Минимальная сумма для поиска
        currency="USDT",
        description=f"Проверка платежа от {user_wallet}"
    )

    if result.get("success") and result.get("payment_found"):
    received_amount = result.get("received_amount", 0)
    logger.info(
        f"USDT платеж подтвержден: {received_amount} USDT от {user_wallet}")
    return {
        "status": "paid",
        "amount": received_amount,
        "transaction_hash": result.get("transaction_hash"),
        "confirmed_at": result.get("confirmed_at")
    }
    else:
    logger.info(
        f"USDT платеж не найден от {user_wallet}: {
            result.get(
                'message',
                'Неизвестная ошибка')}")
    return {
        "status": "pending",
        "amount": 0,
        "message": result.get("message", "Платеж не найден")
    }

    except Exception as e:
        logger.error(f"Ошибка проверки USDT платежа от {user_wallet}: {e}")
        return {
            "status": "error",
            "amount": 0,
            "message": f"Ошибка проверки: {str(e)}"
        }

        async def check_usdt_payment_callback(
                self,
                update: Update,
                context: ContextTypes.DEFAULT_TYPE,
                user_id: int,
                amount: float):
    """Обработчик проверки USDT платежа"""
    query = update.callback_query
    await query.answer()

    # Показываем индикатор загрузки
    await query.edit_message_text("⏳ Проверяем USDT платеж...")

    # Получаем данные о платеже из контекста
    pending_payment = context.user_data.get('pending_payment', {})
    user_wallet = pending_payment.get('user_wallet')

    if not user_wallet:
        await query.edit_message_text("❌ Ошибка: данные о платеже не найдены")
        return

        # Проверяем платеж
    result = await self.check_usdt_payment(user_wallet, amount)

    if result["status"] == "paid":
        # Платеж подтвержден
        transaction_id = pending_payment.get('transaction_id')
        deposit_type = pending_payment.get('deposit_type', '10_days')

        # Обновляем статус транзакции
        self.update_transaction_status(transaction_id, "completed")

        # Обновляем баланс пользователя
        self.update_user_balance(user_id, result["amount"], transaction_id)

        message_text = f"""
✅ ВКЛАД УСПЕШНО ВНЕСЕН!

💰 Сумма: {result['amount']} USDT
📅 Тип вклада: {deposit_type.replace('_', ' ').title()}
🔗 Транзакция: {result.get('transaction_hash', 'N/A')}
⏰ Время подтверждения: {result.get('confirmed_at', 'N/A')}
🆔 ID транзакции: {transaction_id}

🎉 Вклад создан и зачислен на ваш баланс!
💡 Теперь вы будете получать ежедневные выплаты согласно условиям вклада.
        """

        # Очищаем данные о платеже
        context.user_data.pop('pending_payment', None)

        keyboard = [[InlineKeyboardButton(
            "🔙 В главное меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

    elif result["status"] == "pending":
        # Платеж не найден
        message_text = f"""
⏳ ПЛАТЕЖ ЕЩЕ НЕ ПОСТУПИЛ

💰 Ожидаемая сумма: {amount} USDT
👤 От кошелька: {user_wallet}

📋 Проверьте:
• Отправили ли вы точную сумму {amount} USDT
• Правильный ли кошелек получателя
• Прошло ли достаточно времени (1-2 минуты)

💡 Если все правильно, попробуйте проверить еще раз
        """

        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_usdt_{user_id}_{amount}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="deposit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

    else:
        # Ошибка проверки
        message_text = f"""
❌ ОШИБКА ПРОВЕРКИ ПЛАТЕЖА

{result.get('message', 'Неизвестная ошибка')}

💡 Попробуйте проверить еще раз
        """

        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_usdt_{user_id}_{amount}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="deposit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

        async def check_any_amount_payment_callback(
                self,
                update: Update,
                context: ContextTypes.DEFAULT_TYPE,
                user_id: int):
    """Обработчик проверки платежа с любой суммой"""
    query = update.callback_query
    await query.answer()

    # Показываем индикатор загрузки
    await query.edit_message_text("⏳ Проверяем платеж...")

    # Получаем данные о платеже из контекста
    payment_tracking = context.user_data.get('payment_tracking', {})
    user_wallet = payment_tracking.get('user_wallet')

    if not user_wallet:
        await query.edit_message_text("❌ Ошибка: данные о платеже не найдены")
        return

        # Проверяем платеж с любой суммой (минимум 50 USDT)
    result = await self.check_any_amount_payment(user_wallet)

    if result["status"] == "paid":
        # Платеж подтвержден
        deposit_type = payment_tracking.get('deposit_type', '10_days')
        tracking_id = payment_tracking.get('tracking_id')
        received_amount = result["amount"]

        # Создаем транзакцию с полученной суммой
        transaction_id = self.create_user_transaction(
            user_id=user_id,
            amount=received_amount,
            deposit_type=deposit_type,
            wallet_address=user_wallet,
            invoice_id=tracking_id
        )

        # Обновляем баланс пользователя
        self.update_user_balance(user_id, received_amount, transaction_id)

        message_text = f"""
✅ ВКЛАД УСПЕШНО ВНЕСЕН!

💰 Получено: {received_amount} USDT
📅 Тип вклада: {deposit_type.replace('_', ' ').title()}
🔗 Транзакция: {result.get('transaction_hash', 'N/A')}
⏰ Время подтверждения: {result.get('confirmed_at', 'N/A')}
🆔 ID транзакции: {transaction_id}

🎉 Вклад создан и зачислен на ваш баланс!
💡 Теперь вы будете получать ежедневные выплаты согласно условиям вклада.
        """

        # Очищаем данные о платеже
        context.user_data.pop('payment_tracking', None)

        keyboard = [[InlineKeyboardButton(
            "🔙 В главное меню", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

    elif result["status"] == "pending":
        # Платеж не найден
        message_text = f"""
⏳ ПЛАТЕЖ ЕЩЕ НЕ ПОСТУПИЛ

👤 От кошелька: {user_wallet}

📋 Проверьте:
• Отправили ли вы USDT на правильный кошелек
• Прошло ли достаточно времени (1-2 минуты)
• Сумма должна быть не менее 50 USDT

💡 Если все правильно, попробуйте проверить еще раз
        """

        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_any_amount_{user_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="deposit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

    else:
        # Ошибка проверки
        message_text = f"""
❌ ОШИБКА ПРОВЕРКИ ПЛАТЕЖА

{result.get('message', 'Неизвестная ошибка')}

💡 Попробуйте проверить еще раз
        """

        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_any_amount_{user_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="deposit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

        async def handle_message(
                self,
                update: Update,
                context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений"""
    # Очищаем предыдущие сообщения при вводе данных (кроме команды /start)
    await self.cleanup_messages(update, context)

    if context.user_data.get('waiting_for_wallet'):
        wallet_address = update.message.text.strip()

        if len(wallet_address) >= 34 and wallet_address.startswith('T'):
    context.user_data['wallet_address'] = wallet_address
    context.user_data['waiting_for_wallet'] = False

    # Сохраняем адрес кошелька в базе данных
    user_id = update.effective_user.id
    with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE users SET wallet_address = ? WHERE telegram_id = ?
    ''', (wallet_address, user_id))
    conn.commit()

    # Сразу показываем инструкции по оплате
    await self.show_payment_instructions(update, context, wallet_address)
    else:
    await update.message.reply_text(
        "❌ Неверный формат адреса USDT (TRC20). Попробуйте еще раз."
    )
    elif context.user_data.get('waiting_for_withdrawal_amount'):
        # Обработка ввода суммы для вывода
        try:
    amount = float(update.message.text.strip())
    available_amount = context.user_data.get('available_amount', 0)

    if amount < 50:
    await update.message.reply_text("❌ Минимальная сумма для вывода: 50 USDT")
    elif amount > available_amount:
    await update.message.reply_text(f"❌ Максимальная сумма для вывода: {available_amount:.2f} USDT")
    else:
    context.user_data['withdrawal_amount'] = amount
    context.user_data['waiting_for_withdrawal_amount'] = False
    context.user_data['waiting_for_withdrawal_wallet'] = True

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="withdrawal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = f"""
💸 ПОДТВЕРЖДЕНИЕ ВЫВОДА

Сумма: {amount:.2f} USDT

Введите USDT кошелек (TRC20) для получения средств:
• Адрес должен начинаться с 'T'
• Длина не менее 34 символов
    """

    await update.message.reply_text(
        text=message_text,
        reply_markup=reply_markup
    )
    except ValueError:
    await update.message.reply_text("❌ Неверный формат суммы. Введите число (например: 10.5)")
    elif context.user_data.get('waiting_for_custom_amount'):
        # Обработка ввода произвольной суммы
        try:
    amount = float(update.message.text.strip())

    # Проверяем минимальную сумму
    if amount < 50:
    await update.message.reply_text("❌ Минимальная сумма депозита: 50 USDT")
    return

    # Проверяем количество активных вкладов
    user_id = update.effective_user.id
    active_deposits_count = self.get_user_active_deposits_count(user_id)
    if active_deposits_count >= 10:
    await update.message.reply_text(
        f"❌ У вас уже есть {active_deposits_count} активных вкладов\n\n"
        "Максимальное количество активных вкладов: 10\n"
        "Дождитесь выплаты одного из вкладов, чтобы создать новый."
    )
    context.user_data['waiting_for_custom_amount'] = False
    return

    # Обрабатываем сумму как обычный депозит
    context.user_data['waiting_for_custom_amount'] = False
    await self.process_deposit_amount(update, context, str(amount))

    except ValueError:
    await update.message.reply_text("❌ Неверный формат суммы. Введите число (например: 150.5)")
    elif context.user_data.get('waiting_for_withdrawal_wallet'):
        # Обработка ввода кошелька для вывода
        wallet_address = update.message.text.strip()

        if len(wallet_address) >= 34 and wallet_address.startswith('T'):
    amount = context.user_data.get('withdrawal_amount', 0)
    user_id = update.effective_user.id

    # Создаем заявку на вывод
    request_id = self.create_withdrawal_request(
        user_id, amount, wallet_address)

    # Очищаем данные
    context.user_data.pop('withdrawal_amount', None)
    context.user_data.pop('waiting_for_withdrawal_wallet', None)

    keyboard = [[InlineKeyboardButton(
        "🔙 Назад к рефералам", callback_data="referrals")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = f"""
✅ ЗАЯВКА СОЗДАНА

ID заявки: #{request_id}
Сумма: {amount:.2f} USDT
Кошелек: {wallet_address}

Заявка отправлена на рассмотрение администратору.
Вы получите уведомление о результате.
    """

    await update.message.reply_text(
        text=message_text,
        reply_markup=reply_markup
    )
    else:
    await update.message.reply_text(
        "❌ Неверный формат адреса USDT (TRC20). Попробуйте еще раз."
    )
    else:
        await update.message.reply_text("Используйте кнопки меню для навигации")

        async def show_withdrawal_menu(
                self,
                update: Update,
                context: ContextTypes.DEFAULT_TYPE):
    """Показать меню вывода средств"""
    user = update.effective_user

    # Получаем доступную сумму для вывода (общий доход от рефералов)
    available_amount = self.get_total_referral_earned(user.id)

    keyboard = [[InlineKeyboardButton(
        "🔙 Назад к рефералам", callback_data="referrals")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = f"""
💸 ВЫВОД СРЕДСТВ

💰 Доступно к выводу: {available_amount:.2f} USDT

Введите сумму, которую хотите вывести:
• Минимальная сумма: 50 USDT
    """

    # Устанавливаем состояние ожидания ввода суммы
    context.user_data['waiting_for_withdrawal_amount'] = True
    context.user_data['available_amount'] = available_amount

    await self.safe_edit_message(update, message_text, reply_markup)

    async def show_admin_panel(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Показать админ панель"""
    user = update.effective_user

    # Проверяем права администратора
    if not self.is_admin(user.id):
        await self.safe_edit_message(
            update,
            "❌ У вас нет прав администратора",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]])
        )
        return

    keyboard = [
        [InlineKeyboardButton("📋 Заявки на вывод", callback_data="withdrawal_requests")],
        [InlineKeyboardButton("💰 Выплата вкладов", callback_data="deposit_payments")],
        [InlineKeyboardButton("✅ Завершенные платежи", callback_data="completed_payments")],
        [InlineKeyboardButton("📊 Статистика бота", callback_data="bot_statistics")],
        [InlineKeyboardButton("📈 Поступления за 10 дней", callback_data="daily_deposits_stats")],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = """
🔧 АДМИН ПАНЕЛЬ

Выберите действие:
• Заявки на вывод - просмотр и обработка заявок
• Выплата вкладов - расписание выплат по дням (10% за 10 дней)
• Статистика бота - общая информация о боте
    """

    await self.safe_edit_message(update, message_text, reply_markup)

    async def show_withdrawal_requests(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Показать заявки на вывод - по одной заявке с счетчиком"""
    user = update.effective_user

    if not self.is_admin(user.id):
        await self.safe_edit_message(update, "❌ У вас нет прав администратора")
        return

    requests = self.get_withdrawal_requests('pending')

    if not requests:
        message_text = "📋 Нет заявок на вывод"
        keyboard = [[InlineKeyboardButton(
            "🔙 Назад", callback_data="admin_panel")]]
    else:
        # Показываем только первую заявку
        req = requests[0]
        user_name = req.get('first_name', 'Unknown')
        username = f"@{req.get('username', '')}" if req.get('username') else ""

        message_text = f"📋 ЗАЯВКИ НА ВЫВОД\n\n"
        message_text += f"📊 Всего заявок: {len(requests)}\n\n"
        message_text += f"ID: {req['id']}\n"
        message_text += f"Пользователь: {user_name} {username}\n"
        message_text += f"Сумма: {req['amount']:.2f} USDT\n"
        message_text += f"Кошелек: {req['wallet_address']}\n"
        message_text += f"Дата: {req['created_at']}\n"

        keyboard = [
            [InlineKeyboardButton("✅ Рассмотрено", callback_data=f"approve_{req['id']}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await self.safe_edit_message(update, message_text, reply_markup)

    async def show_deposit_payments(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Показать выплаты вкладов по дням"""
    user = update.effective_user

    if not self.is_admin(user.id):
        await self.safe_edit_message(update, "❌ У вас нет прав администратора")
        return

    try:
        # Получаем все выплаты объединенные
        all_payments = self.get_deposit_payments_by_day()
    except Exception as e:
        logger.error(f"Ошибка получения выплат вкладов: {e}")
        await self.safe_edit_message(
            update,
            f"❌ Ошибка получения данных: {e}",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]])
        )
        return

    if not all_payments:
        message_text = "💰 Нет выплат вкладов"
        keyboard = [[InlineKeyboardButton(
            "🔙 Назад", callback_data="admin_panel")]]
    else:
        message_text = "💰 ВЫПЛАТЫ ВКЛАДОВ\n\n"

        # Группируем по дням
        days_dict = {}
        for day_data in all_payments:
    days_remaining, payment_date, deposit_type, payment_count, total_amount, payment_details = day_data

    if days_remaining not in days_dict:
    days_dict[days_remaining] = {
        'date': payment_date,
        'total_count': 0,
        'total_amount': 0,
        'original_amount': 0
    }

    days_dict[days_remaining]['total_count'] += payment_count
    days_dict[days_remaining]['total_amount'] += total_amount

    # Получаем оригинальную сумму для расчета процентов
    original_amount = self.get_original_amount_for_day(
        days_remaining, deposit_type)
    days_dict[days_remaining]['original_amount'] += original_amount

    # Показываем все дни в формате "день/число заявок/общая сумма"
    days_lines = []
    for days_remaining in sorted(days_dict.keys(), reverse=True):
    day_info = days_dict[days_remaining]
    days_lines.append(
        f"{days_remaining}д-{day_info['total_count']}/{day_info['total_amount']:.0f}$")

    # Разбиваем на строки по 6 дней для компактности
    for i in range(0, len(days_lines), 6):
    line = days_lines[i:i + 6]
    message_text += " ".join(line) + "\n"

    message_text += "\n"

    # Показываем подробную информацию о заявке на рассмотрении
    first_payment = self.get_first_urgent_deposit_payment()
    if first_payment:
    user_name = first_payment.get('first_name', 'Unknown')
    username = f"@{first_payment.get('username',
                                     '')}" if first_payment.get('username') else ""

    # Получаем процент вклада и дополнительную информацию
    deposit_type = first_payment.get('deposit_type', '10_days')
    profit_percent = 30 if deposit_type == '30_days' else 8
    deposit_days = 30 if deposit_type == '30_days' else 10

    # Получаем оригинальную сумму вклада
    original_amount = self.get_original_amount_for_payment(first_payment['id'])

    # Рассчитываем процент
    profit_amount = first_payment['amount'] - original_amount

    message_text += "🔍 ЗАЯВКА НА РАССМОТРЕНИИ:\n"
    message_text += f"💰 Первоначальный вклад: {original_amount:.2f} USDT\n"
    message_text += f"💵 Процент прибыли: {
        profit_amount:.2f} USDT ({profit_percent}%)\n"
    message_text += f"🏦 Кошелек: {first_payment['wallet_address']}\n"
    message_text += f"📅 Дата создания: {first_payment['created_at']}\n"
    message_text += f"🆔 ID заявки: #{first_payment['id']}\n"
    message_text += f"💸 НУЖНО ОТПРАТИТЬ: {
        first_payment['amount']:.2f} USDT\n"

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Рассмотрено", callback_data=f"pay_deposit_{
                    first_payment['id']}")], [
            InlineKeyboardButton(
                "🔙 Назад", callback_data="admin_panel")]]
    else:
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await self.safe_edit_message(update, message_text, reply_markup)

    async def show_completed_payments(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Показать завершенные платежи"""
    user = update.effective_user

    if not self.is_admin(user.id):
        await self.safe_edit_message(update, "❌ У вас нет прав администратора")
        return

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()

    # Получаем завершенные платежи
    cursor.execute('''
    SELECT
    dp.id,
    dp.return_amount,
    dp.paid_at,
    dp.deposit_type,
    u.first_name,
    u.username,
    u2.first_name as admin_name
    FROM deposit_payments dp
    JOIN users u ON dp.user_id = u.telegram_id
    LEFT JOIN users u2 ON dp.paid_by = u2.telegram_id
    WHERE dp.status = 'paid'
    ORDER BY dp.paid_at DESC
    LIMIT 20
    ''')

    completed_payments = cursor.fetchall()

    except Exception as e:
        logger.error(f"Ошибка получения завершенных платежей: {e}")
        await self.safe_edit_message(
            update,
            f"❌ Ошибка получения данных: {e}",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]])
        )
        return

    if not completed_payments:
        message_text = "✅ Нет завершенных платежей"
        keyboard = [[InlineKeyboardButton(
            "🔙 Назад", callback_data="admin_panel")]]
    else:
        message_text = "✅ ЗАВЕРШЕННЫЕ ПЛАТЕЖИ\n\n"

        for payment in completed_payments:
    payment_id, amount, paid_at, deposit_type, user_name, username, admin_name = payment

    username_str = f"@{username}" if username else ""
    admin_str = admin_name if admin_name else "Система"
    deposit_type_str = "30-дн" if deposit_type == "30_days" else "10-дн"

    message_text += f"#{payment_id} | {user_name} {username_str}\n"
    message_text += f"💰 {amount:.2f} USDT ({deposit_type_str})\n"
    message_text += f"👤 Выплатил: {admin_str}\n"
    message_text += f"📅 {paid_at}\n\n"

    keyboard = [[InlineKeyboardButton(
        "🔙 Назад", callback_data="admin_panel")]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await self.safe_edit_message(update, message_text, reply_markup)

    async def show_bot_statistics(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику бота"""
    user = update.effective_user

    if not self.is_admin(user.id):
        await self.safe_edit_message(update, "❌ У вас нет прав администратора")
        return

    stats = self.get_bot_statistics()

    message_text = f"""
📊 СТАТИСТИКА БОТА

👥 Всего пользователей: {stats['total_users']}
💰 Общий баланс: {stats['total_balance']:.2f} USDT
💵 Общий доход от рефералов: {stats['total_referral_earned']:.2f} USDT
⏳ Заявок на вывод (ожидают): {stats['pending_withdrawals']}
    """

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await self.safe_edit_message(update, message_text, reply_markup)

    async def show_daily_deposits_stats(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику поступлений за 10 дней"""
    user = update.effective_user

    if not self.is_admin(user.id):
        await self.safe_edit_message(update, "❌ У вас нет прав администратора")
        return

    stats = self.get_daily_deposits_stats()
    daily_stats = stats['daily_stats']
    total_stats = stats['total_stats']

    message_text = "📈 ПОСТУПЛЕНИЯ ЗА 10 ДНЕЙ\n\n"

    # Общая статистика
    if total_stats and total_stats[0] > 0:
        message_text += f"📊 ОБЩАЯ СТАТИСТИКА:\n"
        message_text += f"• Всего депозитов: {total_stats[0]}\n"
        message_text += f"• Общая сумма: {total_stats[1]:.2f} USDT\n"
        message_text += f"• 10-дневные: {total_stats[2]:.2f} USDT\n"
        message_text += f"• 30-дневные: {total_stats[3]:.2f} USDT\n\n"
    else:
        message_text += "📊 ОБЩАЯ СТАТИСТИКА:\n"
        message_text += "• За последние 10 дней поступлений не было\n\n"

        # Статистика по дням
    if daily_stats:
        message_text += "📅 ПО ДНЯМ:\n"
        for day_stat in daily_stats:
    date_str, count, total, amount_10, amount_30 = day_stat
    message_text += f"• {date_str}: {count} деп. ({total:.2f} USDT)\n"
    if amount_10 > 0:
        message_text += f"  └ 10д: {amount_10:.2f} USDT\n"
    if amount_30 > 0:
        message_text += f"  └ 30д: {amount_30:.2f} USDT\n"
    else:
        message_text += "📅 ПО ДНЯМ:\n"
        message_text += "• Нет данных за последние 10 дней\n"

    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await self.safe_edit_message(update, message_text, reply_markup)

    async def approve_withdrawal(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            request_id: str):
    """Одобрить заявку на вывод и показать следующую"""
    user = update.effective_user

    if not self.is_admin(user.id):
        await self.safe_edit_message(update, "❌ У вас нет прав администратора")
        return

        # Одобряем заявку
        self.update_withdrawal_status(int(request_id), 'approved', user.id)

        # Показываем следующую заявку (если есть)
    await self.show_withdrawal_requests(update, context)

    async def pay_deposit(
            self,
            update: Update,
            context: ContextTypes.DEFAULT_TYPE,
            payment_id: str):
    """Обработать выплату депозита и показать следующую"""
    user = update.effective_user

    if not self.is_admin(user.id):
        await self.safe_edit_message(update, "❌ У вас нет прав администратора")
        return

    try:
        # Отмечаем выплату как выполненную
        with sqlite3.connect(DATABASE_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE deposit_payments
    SET status = 'paid', paid_at = CURRENT_TIMESTAMP, paid_by = ?
    WHERE id = ?
    ''', (user.id, payment_id))
    conn.commit()

    logger.info(
        f"Выплата депозита {payment_id} обработана администратором {
            user.id}")

    # Показываем следующую заявку на выплату (если есть)
    await self.show_deposit_payments(update, context)

    except Exception as e:
        logger.error(f"Ошибка обработки выплаты депозита {payment_id}: {e}")
    await self.safe_edit_message(
        update,
        f"❌ Ошибка обработки выплаты: {e}",
        InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]])
    )

    def run(self):
    """Запуск бота"""
    logger.info(
        "🤖 ЗАПУСК БОТА - ВЕРСИЯ: bot_final_backup.py (ПОЛНАЯ ВЕРСИЯ С АДМИНКОЙ)")

    # Запускаем периодическую проверку платежей
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Создаем задачу для периодической проверки
    async def periodic_check():
        while True:
    try:
    await self.check_pending_payments()
    self.cleanup_expired_transactions()
    await asyncio.sleep(30)  # Проверяем каждые 30 секунд
    except Exception as e:
    logger.error(f"Ошибка периодической проверки: {e}")
    await asyncio.sleep(60)  # При ошибке ждем минуту

    # Webhook сервер запускается отдельно
    # Для запуска: python3 webhook_server.py

    # Запускаем периодическую задачу (временно отключено)
    task = None
    # task = loop.create_task(periodic_check())

    try:
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
    logger.info("Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
    finally:
        # Отменяем периодическую задачу
        if task:
    task.cancel()
    # Освобождаем блокировку при завершении
    self._release_lock()
    logger.info("Блокировка освобождена")

    def process_payment_webhook(self, webhook_data: dict):
    """Обработать webhook от платежной системы о получении платежа"""
    try:
        user_wallet = webhook_data.get('user_wallet')
        received_amount = webhook_data.get('amount', 0)
        transaction_hash = webhook_data.get('transaction_hash', '')
        confirmed_at = webhook_data.get('confirmed_at', '')

    logger.info(
        f"Получен webhook о платеже: {received_amount} USDT от {user_wallet}")

    # Проверяем, есть ли ожидаемый платеж от этого кошелька
    if user_wallet in self.pending_payments:
    payment_info = self.pending_payments[user_wallet]
    user_id = payment_info['user_id']
    deposit_type = payment_info['deposit_type']
    tracking_id = payment_info['tracking_id']

    logger.info(
        f"Обрабатываем платеж для пользователя {user_id}: {received_amount} USDT")

    # Создаем транзакцию с полученной суммой
    transaction_id = self.create_user_transaction(
        user_id=user_id,
        amount=received_amount,
        deposit_type=deposit_type,
        wallet_address=user_wallet,
        invoice_id=tracking_id
    )

    # Обновляем баланс пользователя
    self.update_user_balance(user_id, received_amount, transaction_id)

    # Удаляем из ожидаемых платежей
    del self.pending_payments[user_wallet]

    logger.info(
        f"✅ Платеж обработан: {received_amount} USDT для пользователя {user_id}")

    # Отправляем уведомление пользователю (если возможно)
    try:
        # Здесь можно добавить отправку уведомления пользователю
        # Но для этого нужен доступ к application context
    pass
    except Exception as e:
    logger.error(f"Ошибка отправки уведомления пользователю: {e}")

    return {
        "success": True,
        "message": f"Платеж обработан: {received_amount} USDT",
        "transaction_id": transaction_id
    }
    else:
    logger.warning(f"Получен платеж от неизвестного кошелька: {user_wallet}")
    return {
        "success": False,
        "message": "Кошелек не найден в ожидаемых платежах"
    }

    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return {
            "success": False,
            "message": f"Ошибка обработки: {str(e)}"
        }


if __name__ == "__main__":
    bot = FastBot()
    bot.run()
