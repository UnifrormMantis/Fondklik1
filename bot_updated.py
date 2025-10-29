import logging
import sqlite3
import hashlib
import asyncio
import aiohttp
import ssl
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8204117323:AAEe4-1jEKpSkpr13-FYjdSdFeBdbQHpNcY"
DATABASE_PATH = "bot_database.db"
CRYPTO_BOT_TOKEN = "469004:AAFOCI5N0HAQg3RbUKynaRO0cSzADV0x8R"

class FastBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.init_database()
        self.setup_handlers()
    
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
            
            conn.commit()
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def get_or_create_user(self, telegram_id, username, first_name, last_name):
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
            referral_code = hashlib.md5(f"{telegram_id}{datetime.now()}".encode()).hexdigest()[:8]
            
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
    
    def get_total_referral_earned(self, telegram_id):
        """Получить общий доход с рефералов"""
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Создаем таблицу referral_payments если её нет
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
            
            total_earned = cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM referral_payments 
                WHERE referrer_id = ?
            ''', (telegram_id,)).fetchone()[0] or 0
            
            return total_earned
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрый старт"""
        user = update.effective_user
        
        # Быстро создаем пользователя
        user_data = self.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Показываем меню
        await self.show_main_menu(update, context)
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрое меню"""
        await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        keyboard = [
            [InlineKeyboardButton("💰 Внести средства", callback_data="deposit")],
            [InlineKeyboardButton("📊 Мои транзакции", callback_data="transactions")],
            [InlineKeyboardButton("👥 Рефералы", callback_data="referrals")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = """
🔺 Добро пожаловать в Пирамммида!

Этот бот позволяет вам:
• Пополнять баланс через USDT
• Участвовать в реферальной программе
• Получать быстрые и безопасные переводы

Для начала работы выберите нужную опцию ниже.
        """
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=message_text,
                reply_markup=reply_markup
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик кнопок"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "deposit":
            await self.show_deposit_menu(update, context)
        elif data == "enter_wallet":
            await self.enter_wallet(update, context)
        elif data == "transactions":
            await self.show_transactions(update, context)
        elif data == "referrals":
            await self.show_referrals(update, context)
        elif data == "help":
            await self.show_help(update, context)
        elif data == "back_to_menu":
            await self.show_main_menu(update, context)
        elif data.startswith("amount_"):
            amount = data.split("_")[1]
            await self.process_deposit_amount(update, context, amount)
    
    async def show_deposit_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню пополнения"""
        keyboard = [
            [InlineKeyboardButton("💳 Ввести USDT адрес", callback_data="enter_wallet")],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = """
💰 ВНЕСЕНИЕ СРЕДСТВ

Для пополнения баланса:
1. Введите ваш USDT кошелек (TRC20)
2. Выберите сумму пополнения
3. Оплатите через CryptoBot

Нажмите "Ввести USDT адрес" для начала.
        """
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    async def show_transactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    async def show_referrals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать рефералов"""
        user = update.effective_user
        
        # Быстро получаем статистику
        referral_stats = self.get_referral_stats(user.id)
        total_earned = self.get_total_referral_earned(user.id)
        
        # Получаем реферальный код
        user_data = self.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        referral_link = f"https://t.me/{context.bot.username}?start={user_data['referral_code']}"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = f"""
👥 РЕФЕРАЛЬНАЯ СИСТЕМА

🔗 Ваша ссылка: `{referral_link}`

📊 Рефералы:
1-й: {referral_stats['level_1']}
2-й: {referral_stats['level_2']}
3-й: {referral_stats['level_3']}
4-й: {referral_stats['level_4']}
5-й: {referral_stats['level_5']}
6-й: {referral_stats['level_6']}

💰 Всего: {referral_stats['total']} чел.

💵 Общий доход: {total_earned:.2f} USDT

💡 Приглашайте по ссылке → получайте % с пополнений до 6 уровня
        """
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    async def enter_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запрос USDT адреса"""
        context.user_data['waiting_for_wallet'] = True
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="deposit")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = """
💳 ВВОД USDT АДРЕСА

Введите ваш USDT кошелек (TRC20):
• Адрес должен начинаться с 'T'
• Длина не менее 34 символов

Пример: Txxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        """
        
        await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup
        )
    
    async def process_deposit_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE, amount: str):
        """Обработка выбора суммы"""
        try:
            amount_float = float(amount)
            
            # Создаем счет через CryptoBot
            invoice_data = await self.create_invoice(amount_float)
            
            if invoice_data:
                keyboard = [
                    [InlineKeyboardButton("✅ Оплатить", url=invoice_data['pay_url'])],
                    [InlineKeyboardButton("🔙 Назад", callback_data="deposit")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message_text = f"""
💰 СЧЕТ НА ОПЛАТУ

Сумма: {amount_float} USDT
Статус: Ожидает оплаты

Нажмите "Оплатить" для перехода к оплате.
                """
                
                await update.callback_query.edit_message_text(
                    text=message_text,
                    reply_markup=reply_markup
                )
            else:
                await update.callback_query.edit_message_text(
                    text="❌ Ошибка создания счета. Попробуйте позже.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="deposit")]])
                )
                
        except Exception as e:
            logger.error(f"Ошибка обработки суммы: {e}")
            await update.callback_query.edit_message_text(
                text="❌ Ошибка. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="deposit")]])
            )
    
    async def create_invoice(self, amount: float):
        """Создать счет через CryptoBot"""
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                url = "https://pay.crypt.bot/api/createInvoice"
                headers = {
                    "Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN,
                    "Content-Type": "application/json"
                }
                
                data = {
                    "asset": "USDT",
                    "amount": str(amount),
                    "description": f"Пополнение баланса на {amount} USDT",
                    "hidden_message": f"Платеж на сумму {amount} USDT",
                    "paid_btn_name": "openBot",
                    "paid_btn_url": "https://t.me/your_bot_username"
                }
                
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            return result.get("result")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка создания счета: {e}")
            return None

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик сообщений"""
        if context.user_data.get('waiting_for_wallet'):
            wallet_address = update.message.text.strip()
            
            if len(wallet_address) >= 34 and wallet_address.startswith('T'):
                context.user_data['wallet_address'] = wallet_address
                context.user_data['waiting_for_wallet'] = False
                
                # Показываем выбор суммы
                keyboard = [
                    [InlineKeyboardButton("10 USDT", callback_data="amount_10")],
                    [InlineKeyboardButton("25 USDT", callback_data="amount_25")],
                    [InlineKeyboardButton("50 USDT", callback_data="amount_50")],
                    [InlineKeyboardButton("100 USDT", callback_data="amount_100")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="deposit")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message_text = f"""
💳 АДРЕС ПОДТВЕРЖДЕН

Ваш USDT кошелек: `{wallet_address}`

Выберите сумму пополнения:
                """
                
                await update.message.reply_text(
                    text=message_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    "❌ Неверный формат адреса USDT (TRC20). Попробуйте еще раз."
                )
        else:
            await update.message.reply_text("Используйте кнопки меню для навигации")
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск быстрого бота...")
        try:
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")

if __name__ == "__main__":
    bot = FastBot()
    bot.run()
