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
import fcntl
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы
DATABASE_PATH = "bot_database.db"
BOT_TOKEN = "8204117323:AAEe4-1jEKpSkpr13-FYjdSdFeBdbQHpNcY"

class FondklikBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.lock_file = "bot.lock"
        self.lock_fd = None
        
        # Получаем блокировку
        if not self._acquire_lock():
            logger.error("Не удалось получить блокировку. Возможно, бот уже запущен.")
            exit(1)
        
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
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    balance REAL DEFAULT 0.0,
                    referral_code TEXT UNIQUE,
                    referred_by TEXT,
                    wallet_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Добавляем поле wallet_address если его нет
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN wallet_address TEXT')
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Поле уже существует
            
            # Таблица депозитов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deposits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    deposit_type TEXT,
                    profit_percent INTEGER,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
            ''')
            
            # Таблица реферальных выплат
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referral_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    depositor_id INTEGER NOT NULL,
                    deposit_id INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    percentage REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (depositor_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (deposit_id) REFERENCES deposits (id)
                )
            ''')
            
            # Таблица транзакций
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    transaction_type TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
            ''')
            
            conn.commit()

    def setup_handlers(self):
        """Настройка обработчиков"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Добавляем пользователя в базу данных
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (telegram_id, username, first_name, last_name, referral_code)
                VALUES (?, ?, ?, ?, ?)
            ''', (user.id, user.username, user.first_name, user.last_name, f"REF{user.id}"))
            conn.commit()
        
        await self.show_main_menu(update, context)

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /menu"""
        await self.show_main_menu(update, context)

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        user = update.effective_user
        
        keyboard = [
            [InlineKeyboardButton("💰 Внести средства", callback_data="deposit")],
            [InlineKeyboardButton("👥 Реферальная система", callback_data="referral")],
            [InlineKeyboardButton("📊 Ваши вклады", callback_data="my_deposits")],
            [InlineKeyboardButton("💳 Кошелек", callback_data="wallet")],
            [InlineKeyboardButton("ℹ️ Информация", callback_data="info")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = """
🎯 ФондКлик

ФондКлик — это платформа для управления цифровыми активами, где пользователи могут размещать краткосрочные депозиты с фиксированной доходностью.

Пул из размещенных вкладов используется в работе нескольких проектов, прибыль от которых распределяется между пользователями, предоставившими свои средства.

Выберите действие:
        """
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        if update.callback_query:
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_photo(
                photo=logo_photo_id,
                caption=message_text,
                reply_markup=reply_markup
            )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"Button callback received: {data}")
        
        try:
            if data == "deposit":
                await self.show_deposit_options(update, context)
            elif data == "deposit_30":
                await self.start_deposit_process(update, context, "30", 30)
            elif data == "deposit_10":
                await self.start_deposit_process(update, context, "10", 8)
            elif data == "referral":
                await self.show_referral_info(update, context)
            elif data == "my_deposits":
                await self.show_my_deposits(update, context)
            elif data == "wallet":
                await self.show_wallet_menu(update, context)
            elif data == "set_wallet":
                await self.set_wallet(update, context)
            elif data == "change_wallet":
                await self.change_wallet(update, context)
            elif data == "info":
                await self.show_info(update, context)
            elif data == "withdraw_referral":
                await self.show_referral_withdrawal(update, context)
            elif data == "confirm_withdraw_referral":
                await self.confirm_referral_withdrawal(update, context)
            elif data == "back_to_menu":
                await self.show_main_menu(update, context)
            else:
                logger.warning(f"Unknown callback data: {data}")
                await query.edit_message_text("❌ Неизвестная команда. Попробуйте еще раз.")
        except Exception as e:
            logger.error(f"Error in button_callback: {e}")
            await query.edit_message_text("❌ Произошла ошибка. Попробуйте еще раз.")

    async def show_deposit_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать варианты депозитов"""
        keyboard = [
            [InlineKeyboardButton("📅 Внести на 30 дней (30% прибыль)", callback_data="deposit_30")],
            [InlineKeyboardButton("📅 Внести на 10 дней (8% прибыль)", callback_data="deposit_10")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = """
💰 ВНЕСЕНИЕ СРЕДСТВ

Выберите тип депозита:
        """
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
            reply_markup=reply_markup
        )

    async def start_deposit_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE, days: str, profit: int):
        """Начать процесс внесения депозита"""
        context.user_data['deposit_days'] = days
        context.user_data['deposit_profit'] = profit
        
        message_text = f"""💳 ВВОД USDT АДРЕСА

📅 Тип депозита: {days} дней ({profit}% прибыль)

Введите ваш USDT кошелек (TRC20):

⚠️ ВАЖНО:
• Деньги будут выплачиваться ТОЛЬКО на указанный кошелек изменить его будет невозможно 
• Совершайте внесение средств на депозит с этого же кошелька
• Убедитесь, что адрес указан правильно"""
        
        await update.callback_query.edit_message_text(
            text=message_text
        )

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        text = update.message.text.strip()
        
        # Проверяем, ожидаем ли мы ввод кошелька
        if context.user_data.get('awaiting_wallet'):
            # Валидируем адрес кошелька
            if self.validate_wallet_address(text):
                # Сохраняем кошелек в базе данных
                if self.save_wallet_address(user.id, text):
                    message_text = f"""
✅ КОШЕЛЕК УСПЕШНО СОХРАНЕН!

🏦 Ваш кошелек: `{text}`

Теперь вы можете:
• Вносить средства в депозиты
• Выводить средства из реферальной системы
• Получать выплаты по завершенным депозитам

⚠️ ВАЖНО: Все выплаты будут отправлены на этот кошелек
                    """
                    
                    keyboard = [
                        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        text=message_text,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "❌ Ошибка сохранения кошелька. Попробуйте еще раз."
                    )
            else:
                await update.message.reply_text(
                    "❌ Неверный формат кошелька!\n\n"
                    "Кошелек должен:\n"
                    "• Начинаться с 'T'\n"
                    "• Иметь длину 34 символа\n"
                    "• Содержать только буквы и цифры\n\n"
                    "Пример: TExample1234567890123456789012345\n\n"
                    "Попробуйте еще раз:"
                )
            
            # Сбрасываем флаг ожидания
            context.user_data['awaiting_wallet'] = False
            
        elif 'deposit_days' in context.user_data:
            # Старая логика для депозитов (если нужно)
            context.user_data['user_wallet'] = text
            await self.show_payment_instructions(update, context)
        else:
            # Обычное сообщение - показываем меню
            await self.show_main_menu(update, context)

    async def show_payment_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать инструкции по оплате"""
        days = context.user_data['deposit_days']
        profit = context.user_data['deposit_profit']
        user_wallet = context.user_data['user_wallet']
        
        # Генерируем ID отслеживания
        tracking_id = f"usdt{user.id}{int(datetime.now().timestamp())}"
        
        message_text = f"""💰 ВНЕСЕНИЕ ВКЛАДА

📋 Инструкция по оплате:
1️⃣ переведите любую сумму которую вы хотите внести на «кошелек для оплаты» (указан ниже)
2️⃣ Для осуществления перевода используйте ваш кошелек который вы указали ранее (указан ниже)
3️⃣ Нажмите "✅ Проверить платеж" после отправки

🏦 Кошелек для оплаты: TWJ5wQPnJTk2keYXjEgf19i17ZzACBY4Mx
👤 Ваш кошелек (отправитель): {user_wallet}
📅 Тип вклада: {days} Days
🆔 ID отслеживания: {tracking_id}

💡 Вы можете отправить любую сумму от 50 USDT

⚠️ ВАЖНО:
• Используйте для внесения депозита ранее указанный вами кошелек
• Система автоматически определит и зачислит полученную сумму"""
        
        keyboard = [
            [InlineKeyboardButton("✅ Проверить платеж", callback_data=f"check_payment_{tracking_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="deposit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup
        )

    async def show_referral_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать информацию о реферальной системе"""
        user = update.effective_user
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT referral_code FROM users WHERE telegram_id = ?', (user.id,))
            result = cursor.fetchone()
            referral_code = result[0] if result else f"REF{user.id}"
        
        # Получаем детальную статистику рефералов
        stats = self.get_detailed_referral_stats(user.id)
        
        message_text = f"""👥 РЕФЕРАЛЬНАЯ СИСТЕМА

🔗 Ссылка для приглашения:
https://t.me/your_bot?start={referral_code}

📊 Статистика:
• Всего зарегистрировано: {stats['total_registered']} чел.

💰 Пользователи с активными вкладами:

📅 30 дней:
• 1ур: {stats['active_30_level_1']} чел.
• 2ур: {stats['active_30_level_2']} чел.
• 3ур: {stats['active_30_level_3']} чел.

📅 10 дней:
• 1ур: {stats['active_10_level_1']} чел.
• 2ур: {stats['active_10_level_2']} чел.
• 3ур: {stats['active_10_level_3']} чел.

💵 Баланс общего дохода: {stats['total_earned']:.2f} USDT"""
        
        keyboard = [
            [InlineKeyboardButton("💰 Вывод средств", callback_data="withdraw_referral")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )

    async def show_my_deposits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать депозиты пользователя"""
        user = update.effective_user
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT amount, deposit_type, profit_percent, status, created_at, expires_at
                FROM deposits WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user.id,))
            deposits = cursor.fetchall()
        
        if not deposits:
            message_text = """📊 ВАШИ ВКЛАДЫ

У вас пока нет активных депозитов.

Начните с внесения средств для получения прибыли!"""
        else:
            message_text = "📊 ВАШИ ВКЛАДЫ\n\n"
            for deposit in deposits:
                amount, deposit_type, profit_percent, status, created_at, expires_at = deposit
                message_text += f"""💰 {amount} USDT
📅 {deposit_type} дней ({profit_percent}% прибыль)
📊 Статус: {status}
📅 Создан: {created_at}
📅 Истекает: {expires_at}

"""
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )

    async def show_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать информацию о платформе"""
        message_text = """ℹ️ ИНФОРМАЦИЯ

🎯 ФондКлик — это платформа для управления цифровыми активами, где пользователи могут размещать краткосрочные депозиты с фиксированной доходностью.

💡 Как это работает:
• Вы вносите USDT на депозит
• Ваши средства участвуют в прибыльных проектах
• Получаете гарантированную прибыль по истечении срока

🔒 Безопасность:
• Все транзакции защищены блокчейном
• Автоматические выплаты
• Прозрачная отчетность

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

📞 Поддержка: @support_username"""
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )

    async def show_wallet_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню кошелька"""
        user_id = update.effective_user.id
        
        # Получаем текущий адрес кошелька из базы данных
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT wallet_address FROM users WHERE telegram_id = ?', (user_id,))
            result = cursor.fetchone()
            current_wallet = result[0] if result and result[0] else None
        
        if current_wallet:
            # Кошелек уже установлен
            message_text = f"""
💳 ВАШ КОШЕЛЕК

🏦 Адрес кошелька: `{current_wallet}`

Этот кошелек используется для:
• Внесения средств в депозиты
• Вывода средств из реферальной системы
• Выплат по завершенным депозитам

⚠️ ВАЖНО: Все выплаты будут отправлены на этот кошелек
            """
            
            keyboard = [
                [InlineKeyboardButton("✏️ Изменить кошелек", callback_data="change_wallet")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
            ]
        else:
            # Кошелек не установлен
            message_text = """
💳 НАСТРОЙКА КОШЕЛЬКА

Для работы с ФондКлик необходимо указать ваш USDT кошелек (TRC20).

Этот кошелек будет использоваться для:
• Внесения средств в депозиты
• Вывода средств из реферальной системы
• Выплат по завершенным депозитам

⚠️ ВАЖНО: Убедитесь, что адрес указан правильно!
            """
            
            keyboard = [
                [InlineKeyboardButton("➕ Установить кошелек", callback_data="set_wallet")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def set_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс установки кошелька"""
        message_text = """
💳 УСТАНОВКА КОШЕЛЬКА

Введите ваш USDT кошелек (TRC20):

⚠️ ВАЖНО:
• Адрес должен начинаться с "T" (TRC20)
• Длина адреса должна быть 34 символа
• Убедитесь, что адрес указан правильно
• Изменить кошелек можно будет в любое время

Пример: TExample1234567890123456789012345
        """
        
        await update.callback_query.edit_message_text(message_text)
        context.user_data['awaiting_wallet'] = True

    async def change_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс изменения кошелька"""
        message_text = """
💳 ИЗМЕНЕНИЕ КОШЕЛЬКА

Введите новый USDT кошелек (TRC20):

⚠️ ВАЖНО:
• Адрес должен начинаться с "T" (TRC20)
• Длина адреса должна быть 34 символа
• Убедитесь, что адрес указан правильно
• Старый кошелек будет заменен новым

Пример: TExample1234567890123456789012345
        """
        
        await update.callback_query.edit_message_text(message_text)
        context.user_data['awaiting_wallet'] = True

    def validate_wallet_address(self, address: str) -> bool:
        """Валидация TRC20 адреса"""
        if not address:
            return False
        
        # Проверяем, что адрес начинается с T и имеет правильную длину
        if not address.startswith('T'):
            return False
        
        if len(address) != 34:
            return False
        
        # Проверяем, что адрес содержит только допустимые символы
        valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
        if not all(c in valid_chars for c in address):
            return False
        
        return True

    def save_wallet_address(self, user_id: int, wallet_address: str) -> bool:
        """Сохранить адрес кошелька в базе данных"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE users SET wallet_address = ? WHERE telegram_id = ?',
                    (wallet_address, user_id)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения кошелька: {e}")
            return False

    def get_wallet_address(self, user_id: int) -> str:
        """Получить адрес кошелька пользователя"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT wallet_address FROM users WHERE telegram_id = ?', (user_id,))
                result = cursor.fetchone()
                return result[0] if result and result[0] else None
        except Exception as e:
            logger.error(f"Ошибка получения кошелька: {e}")
            return None

    def get_referral_percentage(self, level: int, deposit_type: str) -> float:
        """Получить процент реферального вознаграждения по уровню и типу депозита"""
        percentages = {
            1: {"30": 15.0, "10": 5.0},    # 1-й уровень: 15% (30 дней) / 5% (10 дней)
            2: {"30": 10.0, "10": 3.0},    # 2-й уровень: 10% (30 дней) / 3% (10 дней)
            3: {"30": 5.0, "10": 1.5}      # 3-й уровень: 5% (30 дней) / 1.5% (10 дней)
        }
        
        if level in percentages and deposit_type in percentages[level]:
            return percentages[level][deposit_type]
        return 0.0

    def get_referral_chain(self, user_id: int) -> list:
        """Получить цепочку рефералов (3 уровня)"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Получаем всех рефералов на 3 уровня
                cursor.execute('''
                    WITH RECURSIVE referral_chain AS (
                        -- Базовый случай: прямые рефералы
                        SELECT telegram_id, referred_by, 1 as level
                        FROM users 
                        WHERE referred_by = ?
                        
                        UNION ALL
                        
                        -- Рекурсивный случай: рефералы рефералов
                        SELECT u.telegram_id, u.referred_by, rc.level + 1
                        FROM users u
                        INNER JOIN referral_chain rc ON u.referred_by = rc.telegram_id
                        WHERE rc.level < 3
                    )
                    SELECT telegram_id, level FROM referral_chain
                    ORDER BY level, telegram_id
                ''', (user_id,))
                
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения реферальной цепочки: {e}")
            return []

    def create_referral_payments(self, depositor_id: int, deposit_id: int, amount: float, deposit_type: str):
        """Создать реферальные выплаты для всех уровней"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Получаем цепочку рефералов
                referral_chain = self.get_referral_chain(depositor_id)
                
                for referrer_id, level in referral_chain:
                    percentage = self.get_referral_percentage(level, deposit_type)
                    if percentage > 0:
                        referral_amount = amount * (percentage / 100)
                        
                        cursor.execute('''
                            INSERT INTO referral_payments 
                            (referrer_id, depositor_id, deposit_id, level, amount, percentage, status)
                            VALUES (?, ?, ?, ?, ?, ?, 'pending')
                        ''', (referrer_id, depositor_id, deposit_id, level, referral_amount, percentage))
                
                conn.commit()
                logger.info(f"Созданы реферальные выплаты для депозита {deposit_id}")
                
        except Exception as e:
            logger.error(f"Ошибка создания реферальных выплат: {e}")

    def get_detailed_referral_stats(self, user_id: int) -> dict:
        """Получить детальную статистику рефералов пользователя"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                stats = {
                    'total_registered': 0,
                    'active_30_level_1': 0,
                    'active_30_level_2': 0,
                    'active_30_level_3': 0,
                    'active_10_level_1': 0,
                    'active_10_level_2': 0,
                    'active_10_level_3': 0,
                    'total_earned': 0.0
                }
                
                # Получаем общее количество зарегистрированных рефералов
                cursor.execute('''
                    WITH RECURSIVE referral_chain AS (
                        SELECT telegram_id, referred_by, 1 as level
                        FROM users 
                        WHERE referred_by = ?
                        
                        UNION ALL
                        
                        SELECT u.telegram_id, u.referred_by, rc.level + 1
                        FROM users u
                        INNER JOIN referral_chain rc ON u.referred_by = rc.telegram_id
                        WHERE rc.level < 3
                    )
                    SELECT COUNT(*) FROM referral_chain
                ''', (user_id,))
                result = cursor.fetchone()
                stats['total_registered'] = result[0] if result else 0
                
                # Получаем активные депозиты по уровням и типам
                cursor.execute('''
                    WITH RECURSIVE referral_chain AS (
                        SELECT telegram_id, referred_by, 1 as level
                        FROM users 
                        WHERE referred_by = ?
                        
                        UNION ALL
                        
                        SELECT u.telegram_id, u.referred_by, rc.level + 1
                        FROM users u
                        INNER JOIN referral_chain rc ON u.referred_by = rc.telegram_id
                        WHERE rc.level < 3
                    )
                    SELECT rc.level, d.deposit_type, COUNT(DISTINCT rc.telegram_id) as count
                    FROM referral_chain rc
                    INNER JOIN deposits d ON rc.telegram_id = d.user_id
                    WHERE d.status = 'active'
                    GROUP BY rc.level, d.deposit_type
                ''', (user_id,))
                
                for level, deposit_type, count in cursor.fetchall():
                    if deposit_type == '30':
                        if level == 1:
                            stats['active_30_level_1'] = count
                        elif level == 2:
                            stats['active_30_level_2'] = count
                        elif level == 3:
                            stats['active_30_level_3'] = count
                    elif deposit_type == '10':
                        if level == 1:
                            stats['active_10_level_1'] = count
                        elif level == 2:
                            stats['active_10_level_2'] = count
                        elif level == 3:
                            stats['active_10_level_3'] = count
                
                # Получаем общую сумму заработанного
                cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM referral_payments 
                    WHERE referrer_id = ? AND status = 'paid'
                ''', (user_id,))
                result = cursor.fetchone()
                stats['total_earned'] = result[0] if result else 0.0
                
                return stats
                
        except Exception as e:
            logger.error(f"Ошибка получения детальной статистики рефералов: {e}")
            return {
                'total_registered': 0,
                'active_30_level_1': 0,
                'active_30_level_2': 0,
                'active_30_level_3': 0,
                'active_10_level_1': 0,
                'active_10_level_2': 0,
                'active_10_level_3': 0,
                'total_earned': 0.0
            }

    def get_user_referral_stats(self, user_id: int) -> dict:
        """Получить статистику рефералов пользователя (старый метод для совместимости)"""
        detailed_stats = self.get_detailed_referral_stats(user_id)
        return {
            'level_1_count': detailed_stats['active_30_level_1'] + detailed_stats['active_10_level_1'],
            'level_2_count': detailed_stats['active_30_level_2'] + detailed_stats['active_10_level_2'],
            'level_3_count': detailed_stats['active_30_level_3'] + detailed_stats['active_10_level_3'],
            'total_earned': detailed_stats['total_earned'],
            'pending_earnings': 0.0
        }

    async def show_referral_withdrawal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню вывода реферальных средств"""
        user_id = update.effective_user.id
        
        # Получаем доступный баланс для вывода
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM referral_payments 
                    WHERE referrer_id = ? AND status = 'paid'
                ''', (user_id,))
                result = cursor.fetchone()
                available_balance = result[0] if result else 0.0
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            available_balance = 0.0
        
        # Получаем адрес кошелька
        wallet_address = self.get_wallet_address(user_id)
        
        if not wallet_address:
            message_text = """
💰 ВЫВОД РЕФЕРАЛЬНЫХ СРЕДСТВ

❌ Для вывода средств необходимо указать кошелек.

Сначала перейдите в меню "Кошелек" и укажите ваш USDT кошелек (TRC20).
            """
            keyboard = [
                [InlineKeyboardButton("💳 Настроить кошелек", callback_data="wallet")],
                [InlineKeyboardButton("🔙 Назад", callback_data="referral")]
            ]
        elif available_balance <= 0:
            message_text = """
💰 ВЫВОД РЕФЕРАЛЬНЫХ СРЕДСТВ

❌ У вас нет доступных средств для вывода.

Зарабатывайте больше, приглашая новых пользователей!
            """
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="referral")]
            ]
        else:
            message_text = f"""
💰 ВЫВОД РЕФЕРАЛЬНЫХ СРЕДСТВ

💵 Доступно к выводу: {available_balance:.2f} USDT
🏦 Кошелек: `{wallet_address}`

⚠️ ВАЖНО: 
• Вывод осуществляется на указанный кошелек
• Минимальная сумма вывода: 10 USDT
• Обработка заявки: до 24 часов
            """
            keyboard = [
                [InlineKeyboardButton("💸 Вывести все средства", callback_data="confirm_withdraw_referral")],
                [InlineKeyboardButton("🔙 Назад", callback_data="referral")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def confirm_referral_withdrawal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подтвердить вывод реферальных средств"""
        user_id = update.effective_user.id
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Получаем доступный баланс
                cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM referral_payments 
                    WHERE referrer_id = ? AND status = 'paid'
                ''', (user_id,))
                result = cursor.fetchone()
                available_balance = result[0] if result else 0.0
                
                if available_balance < 10.0:
                    message_text = """
❌ НЕДОСТАТОЧНО СРЕДСТВ

Минимальная сумма для вывода: 10 USDT
                    """
                    keyboard = [
                        [InlineKeyboardButton("🔙 Назад", callback_data="withdraw_referral")]
                    ]
                else:
                    # Создаем заявку на вывод
                    cursor.execute('''
                        INSERT INTO withdrawal_requests (user_id, amount, wallet_address, status)
                        VALUES (?, ?, ?, 'pending')
                    ''', (user_id, available_balance, self.get_wallet_address(user_id)))
                    conn.commit()
                    
                    message_text = f"""
✅ ЗАЯВКА НА ВЫВОД СОЗДАНА

💵 Сумма: {available_balance:.2f} USDT
🏦 Кошелек: `{self.get_wallet_address(user_id)}`
📅 Статус: Ожидает обработки

⏰ Обработка заявки: до 24 часов
                    """
                    keyboard = [
                        [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
                    ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.edit_message_text(
                    text=message_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Ошибка создания заявки на вывод: {e}")
            await update.callback_query.edit_message_text(
                "❌ Произошла ошибка при создании заявки. Попробуйте еще раз."
            )

    def run(self):
        """Запуск бота"""
        logger.info("🤖 ЗАПУСК БОТА - ВЕРСИЯ: bot_fondklik_correct.py (ФОНДКЛИК - ПРАВИЛЬНАЯ ВЕРСИЯ)")
        try:
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        finally:
            self._release_lock()

if __name__ == "__main__":
    bot = FondklikBot()
    bot.run()
