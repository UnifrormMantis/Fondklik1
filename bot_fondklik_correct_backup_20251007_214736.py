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
import time
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
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        try:
            user = update.effective_user
            
            # Проверяем, есть ли реферальный код в команде
            referral_code = None
            if context.args and len(context.args) > 0:
                referral_code = context.args[0]
            
            # Добавляем пользователя в базу данных
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Создаем анонимный код для текущего пользователя
                anonymous_code = f"ANON{user.id}{int(time.time())}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (telegram_id, username, first_name, last_name, referral_code, referred_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user.id, user.username, user.first_name, user.last_name, f"REF{user.id}", referral_code))
                conn.commit()
            
            await self.show_main_menu(update, context)
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            # В случае ошибки пытаемся отправить простое сообщение
            try:
                await update.message.reply_text(
                    "❌ Ошибка инициализации. Попробуйте еще раз.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
                    ]])
                )
            except:
                pass

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /menu"""
        try:
            await self.show_main_menu(update, context)
        except Exception as e:
            logger.error(f"Error in menu_command: {e}")
            try:
                await update.message.reply_text(
                    "❌ Ошибка загрузки меню. Попробуйте еще раз.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
                    ]])
                )
            except:
                pass

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /admin"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        # Показываем админское меню
        message_text = """
🔧 АДМИНСКАЯ ПАНЕЛЬ

Добро пожаловать в админскую панель!

Доступные функции:
• Просмотр статистики
• Управление пользователями
• Мониторинг системы
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.message.reply_photo(
            photo=logo_photo_id,
            caption=message_text,
            reply_markup=reply_markup
        )

    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать админскую панель из главного меню"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        # Показываем админское меню
        message_text = """
🔧 АДМИНСКАЯ ПАНЕЛЬ

Добро пожаловать в админскую панель!

Доступные функции:
• Просмотр статистики
• Управление выплатами
• История выплат
• Мониторинг системы
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("💰 Выплаты депозитов", callback_data="admin_deposit_payments")],
            [InlineKeyboardButton("🎁 Выплаты рефералов", callback_data="admin_referral_payments")],
            [InlineKeyboardButton("📋 История выплат", callback_data="admin_payment_history")],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
            reply_markup=reply_markup
        )

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        try:
            user = update.effective_user
            
            keyboard = [
                [InlineKeyboardButton("💰 Внести средства", callback_data="deposit")],
                [InlineKeyboardButton("👥 Реферальная система", callback_data="referral")],
                [InlineKeyboardButton("📊 Ваши вклады", callback_data="my_deposits")],
                [InlineKeyboardButton("💳 Кошелек", callback_data="wallet")],
                [InlineKeyboardButton("ℹ️ Информация", callback_data="info")]
            ]
            
            # Добавляем кнопку админа, если пользователь является админом
            if self.is_admin(user.id):
                keyboard.append([InlineKeyboardButton("🔧 Админ", callback_data="admin_panel")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message_text = """
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
        except Exception as e:
            logger.error(f"Error in show_main_menu: {e}")
            # В случае ошибки пытаемся отправить простое текстовое сообщение
            try:
                if update.callback_query:
                    await update.callback_query.message.reply_text(
                        "❌ Ошибка загрузки меню. Используйте команду /start",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
                        ]])
                    )
                else:
                    await update.message.reply_text(
                        "❌ Ошибка загрузки меню. Используйте команду /start",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
                        ]])
                    )
            except:
                pass

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
            elif data == "delete_wallet":
                await self.delete_wallet(update, context)
            elif data == "info":
                await self.show_info(update, context)
            elif data == "withdraw_referral":
                await self.show_referral_withdrawal(update, context)
            elif data == "confirm_withdraw_referral":
                await self.confirm_referral_withdrawal(update, context)
            elif data == "admin_panel":
                await self.show_admin_panel(update, context)
            elif data == "admin_stats":
                await self.show_admin_stats(update, context)
            elif data == "admin_deposit_payments":
                await self.show_admin_deposit_payments(update, context)
            elif data == "admin_referral_payments":
                await self.show_admin_referral_payments(update, context)
            elif data == "admin_payment_history":
                await self.show_admin_payment_history(update, context)
            elif data == "admin_deposit_payment_history":
                await self.show_admin_deposit_payment_history(update, context, 0)
            elif data.startswith("deposit_history_page_"):
                page = int(data.split("_")[3])
                await self.show_admin_deposit_payment_history(update, context, page)
            elif data == "admin_referral_payment_history":
                await self.show_admin_referral_payment_history(update, context, 0)
            elif data.startswith("referral_history_page_"):
                page = int(data.split("_")[3])
                await self.show_admin_referral_payment_history(update, context, page)
            elif data == "admin_pending_deposit_payments":
                await self.show_admin_pending_deposit_payments(update, context)
            elif data == "admin_pending_referral_payments":
                await self.show_admin_pending_referral_payments(update, context)
            elif data.startswith("pay_deposit_"):
                await self.process_deposit_payment(update, context, data)
            elif data.startswith("skip_deposit_"):
                await self.skip_deposit_payment(update, context, data)
            elif data.startswith("pay_referral_"):
                await self.process_referral_payment(update, context, data)
            elif data.startswith("skip_referral_"):
                await self.skip_referral_payment(update, context, data)
            elif data == "admin_users":
                await self.show_admin_users(update, context)
            elif data == "noop":
                # Кнопка-заглушка (показывает номер страницы)
                await update.callback_query.answer()
            elif data == "back_to_menu":
                await self.show_main_menu(update, context)
            else:
                logger.warning(f"Unknown callback data: {data}")
                # ID фото логотипа ФондКлик
                logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
                await query.edit_message_media(
                    media=InputMediaPhoto(media=logo_photo_id, caption="❌ Неизвестная команда. Попробуйте еще раз.")
                )
        except Exception as e:
            logger.error(f"Error in button_callback: {e}")
            try:
                # ID фото логотипа ФондКлик
                logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
                
                # Создаем клавиатуру с кнопкой "Главное меню"
                keyboard = [
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_media(
                    media=InputMediaPhoto(media=logo_photo_id, caption="❌ Произошла ошибка. Нажмите 'Главное меню' для восстановления."),
                    reply_markup=reply_markup
                )
            except Exception as inner_e:
                logger.error(f"Error in error handler: {inner_e}")
                # Если даже обработка ошибки не работает, пытаемся отправить новое сообщение
                try:
                    await query.message.reply_text(
                        "❌ Произошла критическая ошибка. Используйте команду /start для восстановления.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
                        ]])
                    )
                except:
                    pass

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
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text)
        )

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            user = update.effective_user
            text = update.message.text.strip()
            
            # Проверяем, ожидаем ли мы ввод кошелька
            if context.user_data.get('awaiting_wallet'):
                logger.info(f"Пользователь {user.id} вводит кошелек: {text}")
                # Валидируем адрес кошелька
                if self.validate_wallet_address(text):
                    logger.info(f"Кошелек {text} прошел валидацию")
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
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
            reply_markup=reply_markup
        )
        except Exception as e:
            logger.error(f"Error in handle_text: {e}")
            try:
                await update.message.reply_text(
                    "❌ Ошибка обработки сообщения. Попробуйте еще раз.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")
                    ]])
                )
            except:
                pass

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
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
            reply_markup=reply_markup
        )

    async def show_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать информацию о платформе"""
        message_text = """ℹ️ ИНФОРМАЦИЯ

Платформа для управления цифровыми активами, где пользователи могут размещать краткосрочные депозиты с фиксированной доходностью.

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
• 🔒 АНОНИМНОСТЬ: Пригласивший человек остается анонимным

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
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
            reply_markup=reply_markup
        )

    async def show_wallet_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню кошелька"""
        user_id = update.effective_user.id
        
        # Получаем текущий адрес кошелька из базы данных
        current_wallet = self.get_wallet_address(user_id)
        
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
                [InlineKeyboardButton("🗑️ Удалить кошелек", callback_data="delete_wallet")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
            ]
        else:
            # Кошелек не установлен
            message_text = """
💳 НАСТРОЙКА КОШЕЛЬКА

Для работы с платформой необходимо указать ваш USDT кошелек (TRC20).

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
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
            reply_markup=reply_markup
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
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text)
        )
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
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text)
        )
        context.user_data['awaiting_wallet'] = True

    async def delete_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить кошелек пользователя"""
        user_id = update.effective_user.id
        
        # Удаляем кошелек из базы данных
        if self.remove_wallet_address(user_id):
            message_text = """
🗑️ КОШЕЛЕК УДАЛЕН

✅ Ваш кошелек успешно удален из системы.

Теперь вы можете:
• Установить новый кошелек
• Продолжить работу без кошелька (некоторые функции будут недоступны)

⚠️ ВАЖНО: Для внесения депозитов необходимо будет установить новый кошелек
            """
            
            keyboard = [
                [InlineKeyboardButton("➕ Установить новый кошелек", callback_data="set_wallet")],
                [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
            ]
        else:
            message_text = """
❌ ОШИБКА УДАЛЕНИЯ

Произошла ошибка при удалении кошелька.
Попробуйте еще раз или обратитесь в поддержку.
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="delete_wallet")],
                [InlineKeyboardButton("🔙 Назад", callback_data="wallet")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
            reply_markup=reply_markup
        )

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
            logger.info(f"Сохранение кошелька для пользователя {user_id}: {wallet_address}")
            
            # Проверяем, существует ли пользователь
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT telegram_id FROM users WHERE telegram_id = ?', (user_id,))
                user_exists = cursor.fetchone()
                logger.info(f"Пользователь {user_id} существует: {user_exists is not None}")
                
                if not user_exists:
                    logger.error(f"Пользователь {user_id} не найден в базе данных")
                    return False
                
                # Используем INSERT OR REPLACE для обновления/создания кошелька
                cursor.execute('''
                    INSERT OR REPLACE INTO user_wallets (user_id, wallet_address, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, wallet_address))
                
                rows_affected = cursor.rowcount
                logger.info(f"Обновлено строк в user_wallets: {rows_affected}")
                
                # Также обновляем кошелек в таблице users для совместимости
                cursor.execute(
                    'UPDATE users SET wallet_address = ? WHERE telegram_id = ?',
                    (wallet_address, user_id)
                )
                rows_affected_users = cursor.rowcount
                logger.info(f"Обновлено строк в users: {rows_affected_users}")
                
                # Проверяем, что кошелек действительно сохранился
                cursor.execute('SELECT wallet_address FROM user_wallets WHERE user_id = ?', (user_id,))
                saved_wallet = cursor.fetchone()
                logger.info(f"Сохраненный кошелек в user_wallets: {saved_wallet[0] if saved_wallet else 'None'}")
                
                conn.commit()
                logger.info("Транзакция закоммичена успешно")
                
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения кошелька: {e}")
            return False

    def remove_wallet_address(self, user_id: int) -> bool:
        """Удалить адрес кошелька из базы данных"""
        try:
            logger.info(f"Удаление кошелька для пользователя {user_id}")
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Удаляем кошелек из таблицы user_wallets
                cursor.execute('DELETE FROM user_wallets WHERE user_id = ?', (user_id,))
                rows_deleted_wallets = cursor.rowcount
                logger.info(f"Удалено строк из user_wallets: {rows_deleted_wallets}")
                
                # Также обновляем кошелек в таблице users для совместимости
                cursor.execute(
                    'UPDATE users SET wallet_address = NULL WHERE telegram_id = ?',
                    (user_id,)
                )
                rows_updated_users = cursor.rowcount
                logger.info(f"Обновлено строк в users: {rows_updated_users}")
                
                conn.commit()
                logger.info("Транзакция удаления закоммичена успешно")
                
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления кошелька: {e}")
            return False

    def is_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь админом"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT telegram_id FROM admins WHERE telegram_id = ?',
                    (user_id,)
                )
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Ошибка проверки админских прав: {e}")
            return False

    def get_wallet_address(self, user_id: int) -> str:
        """Получить адрес кошелька пользователя"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                # Сначала проверяем в новой таблице user_wallets
                cursor.execute('SELECT wallet_address FROM user_wallets WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                if result and result[0]:
                    return result[0]
                
                # Если не найден в user_wallets, проверяем в users (для совместимости)
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
                
                # Получаем всех рефералов на 3 уровня по анонимному коду
                user_referral_code = f"REF{user_id}"
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
                ''', (user_referral_code,))
                
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
                
                # Получаем только прямых рефералов (1-й уровень) по анонимному коду
                user_referral_code = f"REF{user_id}"
                cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (user_referral_code,))
                result = cursor.fetchone()
                stats['total_registered'] = result[0] if result else 0
                
                # Получаем активные депозиты только 1-го уровня
                cursor.execute('''
                    SELECT d.deposit_type, COUNT(DISTINCT u.telegram_id) as count
                    FROM users u
                    INNER JOIN deposits d ON u.telegram_id = d.user_id
                    WHERE u.referred_by = ? AND d.status = 'active'
                    GROUP BY d.deposit_type
                ''', (user_referral_code,))
                
                for deposit_type, count in cursor.fetchall():
                    if deposit_type == '30':
                        stats['active_30_level_1'] = count
                    elif deposit_type == '10':
                        stats['active_10_level_1'] = count
                
                # Получаем общую сумму заработанного
                cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM referral_payments 
                    WHERE referrer_id = ?
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
                    WHERE referrer_id = ?
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
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
            reply_markup=reply_markup
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
                    WHERE referrer_id = ?
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
                
                # ID фото логотипа ФондКлик
                logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
                
                await update.callback_query.edit_message_media(
                    media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"Ошибка создания заявки на вывод: {e}")
            # ID фото логотипа ФондКлик
            logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
            
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(media=logo_photo_id, caption="❌ Произошла ошибка при создании заявки. Попробуйте еще раз.")
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

    async def show_admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать админскую статистику"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            from datetime import datetime, timedelta
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Общее количество пользователей
                cursor.execute('SELECT COUNT(*) FROM users')
                total_users = cursor.fetchone()[0]
                
                # Пользователи с кошельками
                cursor.execute('SELECT COUNT(*) FROM users WHERE wallet_address IS NOT NULL AND wallet_address != ""')
                users_with_wallets = cursor.fetchone()[0]
                
                # Количество админов
                cursor.execute('SELECT COUNT(*) FROM admins')
                total_admins = cursor.fetchone()[0]
                
                # Статистика по дням (последние 10 дней)
                daily_stats = []
                for i in range(9, -1, -1):  # Обратный порядок: от 9 до 0
                    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                    date_short = (datetime.now() - timedelta(days=i)).strftime('%d-%m-%y')
                    
                    # Депозиты за день
                    cursor.execute('''
                        SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                        FROM deposits 
                        WHERE DATE(created_at) = ?
                    ''', (date,))
                    dep_count, dep_sum = cursor.fetchone()
                    
                    # Выплаченные депозиты за день
                    cursor.execute('''
                        SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                        FROM deposits 
                        WHERE DATE(created_at) = ? AND status = 'completed'
                    ''', (date,))
                    dep_paid_count, dep_paid_sum = cursor.fetchone()
                    
                    # Выплаченные рефералы за день
                    cursor.execute('''
                        SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                        FROM referral_payments 
                        WHERE DATE(created_at) = ? AND transaction_id IS NOT NULL
                    ''', (date,))
                    ref_paid_count, ref_paid_sum = cursor.fetchone()
                    
                    daily_stats.append({
                        'date': date_short,
                        'dep_count': dep_count,
                        'dep_sum': dep_sum,
                        'dep_paid_count': dep_paid_count,
                        'dep_paid_sum': dep_paid_sum,
                        'ref_paid_count': ref_paid_count,
                        'ref_paid_sum': ref_paid_sum
                    })
        
            message_text = f"""
📊 АДМИНСКАЯ СТАТИСТИКА

👥 Пользователи:
• Всего пользователей: {total_users}
• С кошельками: {users_with_wallets}
• Администраторов: {total_admins}

📈 СТАТИСТИКА ПО ДНЯМ (последние 10 дней):
"""
            
            for stat in daily_stats:
                message_text += f"""
{stat['date']} деп/{stat['dep_count']}/{stat['dep_sum']:.2f} выпл.вклад/{stat['dep_paid_count']}/{stat['dep_paid_sum']:.2f} выпл.реф/{stat['ref_paid_count']}/{stat['ref_paid_sum']:.2f}"""
            
            message_text += f"""

🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # ID фото логотипа ФондКлик
            logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
            
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            await update.callback_query.answer("❌ Ошибка получения статистики")

    async def show_admin_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список пользователей"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT telegram_id, username, first_name, wallet_address, created_at 
                    FROM users 
                    ORDER BY created_at DESC 
                    LIMIT 10
                ''')
                users = cursor.fetchall()
            
            message_text = "👥 ПОСЛЕДНИЕ 10 ПОЛЬЗОВАТЕЛЕЙ\n\n"
            
            for user_data in users:
                telegram_id, username, first_name, wallet_address, created_at = user_data
                wallet_status = "✅" if wallet_address else "❌"
                message_text += f"• {first_name} (@{username})\n"
                message_text += f"  ID: {telegram_id}\n"
                message_text += f"  Кошелек: {wallet_status}\n"
                message_text += f"  Регистрация: {created_at[:10]}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_users")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # ID фото логотипа ФондКлик
            logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
            
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            await update.callback_query.answer("❌ Ошибка получения списка пользователей")

    async def show_admin_deposit_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать управление выплатами депозитов"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            from datetime import datetime, timedelta
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Статистика по дням (последние 30 дней)
                daily_stats = []
                for i in range(30):
                    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                    date_short = (datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y')
                    
                    # Выплаченные депозиты за день
                    cursor.execute('''
                        SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                        FROM deposits 
                        WHERE DATE(created_at) = ? AND status = 'completed'
                    ''', (date,))
                    paid_count, paid_sum = cursor.fetchone()
                    
                    daily_stats.append({
                        'date': date_short,
                        'count': paid_count,
                        'sum': paid_sum
                    })
                
                # Ожидающие выплаты
                cursor.execute('''
                    SELECT COUNT(*) FROM deposits WHERE status = 'pending'
                ''')
                pending_deposits = cursor.fetchone()[0]
            
            # Получаем статистику на сегодня
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                FROM deposits 
                WHERE DATE(created_at) = ? AND status = 'pending'
            ''', (today,))
            today_count, today_sum = cursor.fetchone()
            
            message_text = """
💰 УПРАВЛЕНИЕ ВЫПЛАТАМИ ДЕПОЗИТОВ

📊 Статистика по дням (последние 30 дней):
"""
            
            for stat in daily_stats:
                if stat['count'] > 0:  # Показываем только дни с выплатами
                    message_text += f"\n{stat['date']}/{stat['count']}/{stat['sum']:.0f}$"
            
            message_text += f"""

📅 Сегодня кол-во заявок: {today_count}; общ. сумма: {today_sum:.0f}$

🔧 Доступные действия:
• Просмотр ожидающих выплат
• Индивидуальная обработка
            """
            
            keyboard = [
                [InlineKeyboardButton("📋 Ожидающие выплаты", callback_data="admin_pending_deposit_payments")],
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # ID фото логотипа ФондКлик
            logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
            
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения данных о выплатах депозитов: {e}")
            await update.callback_query.answer("❌ Ошибка получения данных")

    async def show_admin_referral_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать управление выплатами рефералов"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            from datetime import datetime, timedelta
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Статистика по дням (последние 30 дней)
                daily_stats = []
                for i in range(30):
                    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                    date_short = (datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y')
                    
                    # Выплаченные рефералы за день
                    cursor.execute('''
                        SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                        FROM referral_payments 
                        WHERE DATE(created_at) = ? AND transaction_id IS NOT NULL
                    ''', (date,))
                    paid_count, paid_sum = cursor.fetchone()
                    
                    daily_stats.append({
                        'date': date_short,
                        'count': paid_count,
                        'sum': paid_sum
                    })
                
                # Ожидающие выплаты
                cursor.execute('''
                    SELECT COUNT(*) FROM referral_payments WHERE transaction_id IS NULL
                ''')
                pending_referrals = cursor.fetchone()[0]
            
            # Получаем статистику на сегодня
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*), COALESCE(SUM(amount), 0) 
                FROM referral_payments 
                WHERE DATE(created_at) = ? AND transaction_id IS NULL
            ''', (today,))
            today_count, today_sum = cursor.fetchone()
            
            message_text = """
🎁 УПРАВЛЕНИЕ ВЫПЛАТАМИ РЕФЕРАЛОВ

📊 Статистика по дням (последние 30 дней):
"""
            
            for stat in daily_stats:
                if stat['count'] > 0:  # Показываем только дни с выплатами
                    message_text += f"\n{stat['date']}/{stat['count']}/{stat['sum']:.0f}$"
            
            message_text += f"""

📅 Сегодня кол-во заявок: {today_count}; общ. сумма: {today_sum:.0f}$

🔧 Доступные действия:
• Просмотр ожидающих выплат
• Индивидуальная обработка
            """
            
            keyboard = [
                [InlineKeyboardButton("📋 Ожидающие выплаты", callback_data="admin_pending_referral_payments")],
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # ID фото логотипа ФондКлик
            logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
            
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения данных о выплатах рефералов: {e}")
            await update.callback_query.answer("❌ Ошибка получения данных")

    async def show_admin_payment_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать историю выплат"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        message_text = """
📋 ИСТОРИЯ ВЫПЛАТ

Выберите тип истории для просмотра:

• История выплат вкладов - просмотр всех выплаченных депозитов
• История выплат рефералов - просмотр всех выплаченных реферальных бонусов
        """
        
        keyboard = [
            [InlineKeyboardButton("💰 История выплат вкладов", callback_data="admin_deposit_payment_history")],
            [InlineKeyboardButton("🎁 История выплат рефералов", callback_data="admin_referral_payment_history")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # ID фото логотипа ФондКлик
        logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
        
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
            reply_markup=reply_markup
        )

    async def show_admin_deposit_payment_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
        """Показать историю выплат вкладов с пагинацией"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Получаем общую статистику
                cursor.execute('''
                    SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM deposits WHERE status = 'completed'
                ''')
                total_stats = cursor.fetchone()
                total_deposits = total_stats[0]
                total_amount = total_stats[1] or 0
                
                # Получаем только последние 40 записей, затем пагинируем по 4
                # Сначала получаем общее количество записей (максимум 40)
                cursor.execute('''
                    SELECT COUNT(*) FROM deposits WHERE status = 'completed'
                ''')
                total_completed = cursor.fetchone()[0]
                max_records = min(40, total_completed)
                
                # Получаем записи для текущей страницы (4 записи на страницу)
                offset = page * 4
                cursor.execute('''
                    SELECT d.amount, d.status, d.created_at, u.first_name, u.username, u.wallet_address
                    FROM deposits d
                    JOIN users u ON d.user_id = u.telegram_id
                    WHERE d.status = 'completed'
                    ORDER BY d.created_at DESC
                    LIMIT 4 OFFSET ?
                ''', (offset,))
                deposits = cursor.fetchall()
            
            # Формируем сообщение (расширенный формат с полным адресом кошелька)
            total_pages = (max_records + 3) // 4  # Пересчитываем страницы для 4 записей на страницу
            message_text = f"""💰 ИСТОРИЯ ВЫПЛАТ ВКЛАДОВ

📊 Показано: {max_records} из {total_deposits} | Сумма: {total_amount:.0f}$ | Стр. {page + 1}/{total_pages}:
"""
            
            for i, deposit in enumerate(deposits):
                amount, status, created_at, first_name, username, wallet_address = deposit
                # Полный адрес кошелька на отдельной строке
                wallet_full = wallet_address or 'N/A'
                date_str = created_at[:10] if created_at else 'N/A'
                
                # Обратная нумерация: самые старые записи имеют номер 1
                # max_records - (offset + i) дает обратный порядок
                unique_number = max_records - (offset + i)
                
                # Формат: уникальный номер, сумма, имя, дата на одной строке, кошелек на отдельной строке
                message_text += f"\n{unique_number}. ✅ {amount:.0f}$ | {first_name} | {date_str}"
                message_text += f"\n💳 {wallet_full}"
                message_text += "\n"  # Пустая строка для разделения
            
            # Формируем клавиатуру с пагинацией
            keyboard = []
            
            # Кнопки навигации
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"deposit_history_page_{page-1}"))
            
            # Показываем текущую страницу и общее количество страниц
            nav_buttons.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
            
            if offset + 4 < max_records:
                nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"deposit_history_page_{page+1}"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            # Кнопки управления
            keyboard.extend([
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_deposit_payment_history")],
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_payment_history")]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # ID фото логотипа ФондКлик
            logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
            
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения истории выплат вкладов: {e}")
            await update.callback_query.answer("❌ Ошибка получения истории")

    async def show_admin_referral_payment_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
        """Показать историю выплат рефералов с пагинацией"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM referral_payments WHERE transaction_id IS NOT NULL
                ''')
                total_stats = cursor.fetchone()
                total_referrals = total_stats[0]
                total_amount = total_stats[1] or 0
                
                # Получаем только последние 40 записей, затем пагинируем по 4
                max_records = min(40, total_referrals)
                
                # Получаем записи для текущей страницы (4 записи на страницу)
                offset = page * 4
                cursor.execute('''
                    SELECT rp.amount, rp.created_at, u1.first_name as referrer_name, u1.username as referrer_username,
                           u2.first_name as referred_name, u2.username as referred_username, rp.level, u1.wallet_address as referrer_wallet
                    FROM referral_payments rp
                    JOIN users u1 ON rp.referrer_id = u1.telegram_id
                    JOIN users u2 ON rp.referred_id = u2.telegram_id
                    WHERE rp.transaction_id IS NOT NULL
                    ORDER BY rp.created_at DESC
                    LIMIT 4 OFFSET ?
                ''', (offset,))
                referrals = cursor.fetchall()
            
            # Формируем сообщение
            total_pages = (max_records + 3) // 4
            message_text = f"""🎁 ИСТОРИЯ ВЫПЛАТ РЕФЕРАЛОВ
            
📊 Показано: {max_records} из {total_referrals} | Сумма: {total_amount:.0f}$ | Стр. {page + 1}/{total_pages}:
"""
            
            for i, referral in enumerate(referrals):
                amount, created_at, referrer_name, referrer_username, referred_name, referred_username, level, referrer_wallet = referral
                # Обратная нумерация: самые старые записи имеют номер 1
                # max_records - (offset + i) дает обратный порядок
                unique_number = max_records - (offset + i)
                message_text += f"\n{unique_number}. ✅ {amount:.0f}$ | {referrer_name} | {referrer_wallet or 'N/A'} | L{level} | {created_at[:10]}"
            
            # Формируем клавиатуру с пагинацией
            keyboard = []
            
            # Кнопки навигации
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"referral_history_page_{page-1}"))
            
            # Показываем текущую страницу и общее количество страниц
            nav_buttons.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
            
            if offset + 4 < max_records:
                nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"referral_history_page_{page+1}"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            # Кнопки управления
            keyboard.extend([
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_referral_payment_history")],
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_payment_history")]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # ID фото логотипа ФондКлик
            logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
            
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения истории выплат рефералов: {e}")
            await update.callback_query.answer("❌ Ошибка получения истории")

    async def show_admin_pending_deposit_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать ожидающие выплаты депозитов"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT d.id, d.amount, d.created_at, d.deposit_type, d.profit_percent, u.first_name, u.username, u.wallet_address
                    FROM deposits d
                    JOIN users u ON d.user_id = u.telegram_id
                    WHERE d.status = 'pending'
                    ORDER BY d.created_at ASC
                    LIMIT 1
                ''')
                deposit = cursor.fetchone()
                
                if not deposit:
                    message_text = """
💰 ОЖИДАЮЩИЕ ВЫПЛАТЫ ДЕПОЗИТОВ

✅ Нет заявок на выплату депозитов
                    """
                    keyboard = [
                        [InlineKeyboardButton("🔙 Назад", callback_data="admin_deposit_payments")]
                    ]
                else:
                    deposit_id, amount, created_at, deposit_type, profit_percent, first_name, username, wallet_address = deposit
                    
                    # Рассчитываем сумму к выплате (включая проценты)
                    payout_amount = amount * (1 + profit_percent / 100)
                    
                    # Определяем срок в днях
                    duration_days = 10 if deposit_type == '10_days' else 30
                    
                    message_text = f"""
💰 ОЖИДАЮЩИЕ ВЫПЛАТЫ ДЕПОЗИТОВ

📋 Заявка #{deposit_id}:
👤 Пользователь: {first_name} (@{username})
💳 Кошелек: {wallet_address or 'Не указан'}
💰 Изначальный вклад: {amount:.2f} USDT
📅 Срок вклада: {duration_days} дней
💸 К выплате: {payout_amount:.2f} USDT
📆 Дата создания: {created_at[:16]}
                    """
                    
                    keyboard = [
                        [InlineKeyboardButton("✅ Рассмотрено", callback_data=f"pay_deposit_{deposit_id}")],
                        [InlineKeyboardButton("⏭️ Отложить", callback_data=f"skip_deposit_{deposit_id}")],
                        [InlineKeyboardButton("🔙 Назад", callback_data="admin_deposit_payments")]
                    ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # ID фото логотипа ФондКлик
                logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
                
                await update.callback_query.edit_message_media(
                    media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"Ошибка получения ожидающих выплат депозитов: {e}")
            await update.callback_query.answer("❌ Ошибка получения данных")

    async def show_admin_pending_referral_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать ожидающие выплаты рефералов"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT rp.id, rp.amount, rp.created_at, rp.level, 
                           u1.first_name as referrer_name, u1.username as referrer_username, u1.wallet_address as referrer_wallet,
                           u2.first_name as referred_name, u2.username as referred_username
                    FROM referral_payments rp
                    JOIN users u1 ON rp.referrer_id = u1.telegram_id
                    JOIN users u2 ON rp.referred_id = u2.telegram_id
                    WHERE rp.transaction_id IS NULL
                    ORDER BY rp.created_at ASC
                    LIMIT 1
                ''')
                referral = cursor.fetchone()
                
                if not referral:
                    message_text = """
🎁 ОЖИДАЮЩИЕ ВЫПЛАТЫ РЕФЕРАЛОВ

✅ Нет заявок на выплату рефералов
                    """
                    keyboard = [
                        [InlineKeyboardButton("🔙 Назад", callback_data="admin_referral_payments")]
                    ]
                else:
                    ref_id, amount, created_at, level, referrer_name, referrer_username, referrer_wallet, referred_name, referred_username = referral
                    
                    message_text = f"""
🎁 ОЖИДАЮЩИЕ ВЫПЛАТЫ РЕФЕРАЛОВ

📋 Заявка #{ref_id}:
👤 Реферер: {referrer_name} (@{referrer_username})
💳 Кошелек: {referrer_wallet or 'Не указан'}
👥 Приглашенный: {referred_name} (@{referred_username})
🎯 Уровень: {level}
💸 К выплате: {amount:.2f} USDT
📆 Дата создания: {created_at[:16]}
                    """
                    
                    keyboard = [
                        [InlineKeyboardButton("✅ Рассмотрено", callback_data=f"pay_referral_{ref_id}")],
                        [InlineKeyboardButton("⏭️ Отложить", callback_data=f"skip_referral_{ref_id}")],
                        [InlineKeyboardButton("🔙 Назад", callback_data="admin_referral_payments")]
                    ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # ID фото логотипа ФондКлик
                logo_photo_id = "AgACAgIAAxkBAAECb6lo4pNb_THx3Ojg-ov8rTYpetqHmgACz_8xGwgeEEvwJK5Ngw3vdwEAAwIAA3kAAzYE"
                
                await update.callback_query.edit_message_media(
                    media=InputMediaPhoto(media=logo_photo_id, caption=message_text),
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"Ошибка получения ожидающих выплат рефералов: {e}")
            await update.callback_query.answer("❌ Ошибка получения данных")

    async def process_deposit_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Обработать выплату депозита"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            deposit_id = int(data.split("_")[2])
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Обновляем статус депозита на 'completed'
                cursor.execute('''
                    UPDATE deposits 
                    SET status = 'completed' 
                    WHERE id = ? AND status = 'pending'
                ''', (deposit_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    await update.callback_query.answer("✅ Выплата обработана")
                    
                    # Показываем следующую заявку
                    await self.show_admin_pending_deposit_payments(update, context)
                else:
                    await update.callback_query.answer("❌ Заявка не найдена")
                    
        except Exception as e:
            logger.error(f"Ошибка обработки выплаты депозита: {e}")
            await update.callback_query.answer("❌ Ошибка обработки")

    async def process_referral_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Обработать выплату реферала"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            referral_id = int(data.split("_")[2])
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Создаем транзакцию для реферальной выплаты
                cursor.execute('''
                    INSERT INTO transactions (user_id, amount, transaction_type, status, created_at)
                    VALUES (?, ?, 'referral_payment', 'completed', CURRENT_TIMESTAMP)
                ''', (referral_id, 0))  # amount будет обновлен ниже
                
                transaction_id = cursor.lastrowid
                
                # Обновляем реферальную выплату
                cursor.execute('''
                    UPDATE referral_payments 
                    SET transaction_id = ? 
                    WHERE id = ? AND transaction_id IS NULL
                ''', (transaction_id, referral_id))
                
                if cursor.rowcount > 0:
                    # Обновляем сумму в транзакции
                    cursor.execute('''
                        SELECT amount FROM referral_payments WHERE id = ?
                    ''', (referral_id,))
                    amount = cursor.fetchone()[0]
                    
                    cursor.execute('''
                        UPDATE transactions SET amount = ? WHERE id = ?
                    ''', (amount, transaction_id))
                    
                    conn.commit()
                    await update.callback_query.answer("✅ Выплата обработана")
                    
                    # Показываем следующую заявку
                    await self.show_admin_pending_referral_payments(update, context)
                else:
                    await update.callback_query.answer("❌ Заявка не найдена")
                    
        except Exception as e:
            logger.error(f"Ошибка обработки выплаты реферала: {e}")
            await update.callback_query.answer("❌ Ошибка обработки")

    async def skip_deposit_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Отложить выплату депозита (переместить в конец очереди)"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            deposit_id = int(data.split("_")[2])
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Обновляем дату создания на текущую (перемещаем в конец очереди)
                cursor.execute('''
                    UPDATE deposits 
                    SET created_at = CURRENT_TIMESTAMP 
                    WHERE id = ? AND status = 'pending'
                ''', (deposit_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    await update.callback_query.answer("⏭️ Заявка отложена")
                    
                    # Показываем следующую заявку
                    await self.show_admin_pending_deposit_payments(update, context)
                else:
                    await update.callback_query.answer("❌ Заявка не найдена")
                    
        except Exception as e:
            logger.error(f"Ошибка отложения выплаты депозита: {e}")
            await update.callback_query.answer("❌ Ошибка обработки")

    async def skip_referral_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Отложить выплату реферала (переместить в конец очереди)"""
        user = update.effective_user
        
        # Проверяем админские права
        if not self.is_admin(user.id):
            await update.callback_query.answer("❌ У вас нет прав администратора")
            return
        
        try:
            referral_id = int(data.split("_")[2])
            
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Обновляем дату создания на текущую (перемещаем в конец очереди)
                cursor.execute('''
                    UPDATE referral_payments 
                    SET created_at = CURRENT_TIMESTAMP 
                    WHERE id = ? AND transaction_id IS NULL
                ''', (referral_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    await update.callback_query.answer("⏭️ Заявка отложена")
                    
                    # Показываем следующую заявку
                    await self.show_admin_pending_referral_payments(update, context)
                else:
                    await update.callback_query.answer("❌ Заявка не найдена")
                    
        except Exception as e:
            logger.error(f"Ошибка отложения выплаты реферала: {e}")
            await update.callback_query.answer("❌ Ошибка обработки")

if __name__ == "__main__":
    bot = FondklikBot()
    bot.run()
