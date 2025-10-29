#!/usr/bin/env python3
"""
Примеры кода для использования Payment Bot API в основном боте
"""

# =============================================================================
# ИМПОРТЫ И НАСТРОЙКИ
# =============================================================================

from payment_client_integration import PaymentClient
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Настройки
PAYMENT_API_URL = "http://localhost:8001"
PAYMENT_API_KEY = "rsG7Hzt0EaEY5ZoEH4eE96SiY234qpiSYg5d92xrSm4"
DATABASE_PATH = "bot_database.db"

# Инициализация PaymentClient
payment_client = PaymentClient(PAYMENT_API_KEY, PAYMENT_API_URL)

# =============================================================================
# ПРИМЕР 1: КОМАНДА /WALLET
# =============================================================================

async def wallet_command_example(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пример команды для указания кошелька пользователя"""
    user_id = update.effective_user.id
    
    # Проверяем, есть ли кошелек в сообщении
    if len(context.args) < 1:
        await update.message.reply_text(
            "💳 **Укажите ваш кошелек**\n\n"
            "Использование: `/wallet TYourWalletAddress123456789`\n\n"
            "Этот кошелек будет использоваться для проверки ваших платежей."
        )
        return
    
    wallet_address = context.args[0]
    
    # Сохраняем кошелек в базу данных
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET wallet_address = ? WHERE telegram_id = ?
        ''', (wallet_address, user_id))
        conn.commit()
    
    await update.message.reply_text(
        f"✅ **Кошелек сохранен!**\n\n"
        f"📱 Ваш кошелек: `{wallet_address}`\n\n"
        f"Теперь вы можете использовать команду `/pay` для пополнения баланса."
    )

# =============================================================================
# ПРИМЕР 2: КОМАНДА /PAY
# =============================================================================

async def pay_command_example(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пример команды для пополнения баланса"""
    user_id = update.effective_user.id
    
    # Получаем кошелек пользователя
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT wallet_address FROM users WHERE telegram_id = ?', (user_id,))
        result = cursor.fetchone()
    
    if not result or not result[0]:
        await update.message.reply_text(
            "❌ **Сначала укажите ваш кошелек**\n\n"
            "Используйте команду: `/wallet TYourWalletAddress123456789`"
        )
        return
    
    user_wallet = result[0]
    
    # 🔥 КЛЮЧЕВОЙ МОМЕНТ: Запрашиваем актуальный кошелек через API
    response = payment_client.get_payment_wallet(user_wallet)
    
    if not response.get('success'):
        await update.message.reply_text(f"❌ Ошибка получения кошелька: {response.get('error')}")
        return
    
    active_wallet = response['wallet_address']
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Проверить платеж", callback_data="check_payment")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_payment")]
    ])
    
    await update.message.reply_text(
        f"💳 **Пополнение баланса**\n\n"
        f"📱 Ваш кошелек: `{user_wallet}`\n"
        f"🏦 Кошелек для оплаты: `{active_wallet}`\n\n"
        f"Переведите средства на указанный кошелек, "
        f"затем нажмите кнопку 'Проверить платеж'",
        reply_markup=keyboard
    )

# =============================================================================
# ПРИМЕР 3: ПРОВЕРКА ПЛАТЕЖЕЙ
# =============================================================================

async def check_payment_callback_example(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пример проверки платежа пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Получаем кошелек пользователя
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT wallet_address FROM users WHERE telegram_id = ?', (user_id,))
        result = cursor.fetchone()
    
    if not result or not result[0]:
        await query.edit_message_text("❌ Кошелек не найден")
        return
    
    user_wallet = result[0]
    
    # 🔥 КЛЮЧЕВОЙ МОМЕНТ: Проверяем платежи через API
    response = payment_client.check_user_payments(user_wallet)
    
    if not response.get('success'):
        await query.edit_message_text(f"❌ Ошибка: {response.get('error')}")
        return
    
    payments = response.get('payments', [])
    
    if not payments:
        await query.edit_message_text("⏳ Платеж еще не поступил. Попробуйте позже.")
        return
    
    # Обрабатываем платежи
    total_amount = 0
    for payment in payments:
        if payment['confirmed']:
            total_amount += payment['amount']
            
            # Обновляем баланс
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET balance = balance + ? WHERE telegram_id = ?
                ''', (payment['amount'], user_id))
                conn.commit()
    
    if total_amount > 0:
        await query.edit_message_text(
            f"✅ **Платеж подтвержден!**\n\n"
            f"💰 Зачислено: {total_amount} USDT\n"
            f"📱 Ваш кошелек: `{user_wallet}`\n\n"
            f"Используйте команду `/balance` для проверки баланса."
        )
    else:
        await query.edit_message_text("⏳ Платеж еще не поступил. Попробуйте позже.")

# =============================================================================
# ПРИМЕР 4: КОМАНДА /BALANCE
# =============================================================================

async def balance_command_example(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пример команды для проверки баланса"""
    user_id = update.effective_user.id
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE telegram_id = ?', (user_id,))
        result = cursor.fetchone()
    
    balance = result[0] if result else 0.0
    
    await update.message.reply_text(
        f"💰 **Ваш баланс**\n\n"
        f"💵 Баланс: {balance} USDT\n"
        f"📱 ID: {user_id}"
    )

# =============================================================================
# ПРИМЕР 5: ОБРАБОТКА ОШИБОК
# =============================================================================

async def safe_payment_operation_example(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пример безопасной операции с обработкой ошибок"""
    try:
        # Получаем кошелек пользователя
        user_wallet = "TUserWallet123456789"  # В реальном коде из базы данных
        
        # Запрашиваем актуальный кошелек
        response = payment_client.get_payment_wallet(user_wallet)
        
        # Проверяем успешность запроса
        if not response.get('success'):
            error_msg = response.get('error', 'Неизвестная ошибка')
            await update.message.reply_text(f"❌ Ошибка API: {error_msg}")
            return
        
        # Получаем кошелек
        active_wallet = response['wallet_address']
        
        # Показываем результат
        await update.message.reply_text(
            f"✅ **Кошелек получен!**\n\n"
            f"📱 Ваш кошелек: `{user_wallet}`\n"
            f"🏦 Активный кошелек: `{active_wallet}`"
        )
        
    except Exception as e:
        # Логируем ошибку
        print(f"Ошибка в safe_payment_operation: {e}")
        
        # Показываем пользователю понятное сообщение
        await update.message.reply_text(
            "❌ **Произошла ошибка**\n\n"
            "Попробуйте позже или обратитесь к администратору."
        )

# =============================================================================
# ПРИМЕР 6: РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ
# =============================================================================

def register_payment_handlers_example(application):
    """Пример регистрации обработчиков команд"""
    from telegram.ext import CommandHandler, CallbackQueryHandler
    
    # Команды
    application.add_handler(CommandHandler("wallet", wallet_command_example))
    application.add_handler(CommandHandler("pay", pay_command_example))
    application.add_handler(CommandHandler("balance", balance_command_example))
    
    # Callback queries
    application.add_handler(CallbackQueryHandler(check_payment_callback_example, pattern="^check_payment$"))

# =============================================================================
# ПРИМЕР 7: ТЕСТИРОВАНИЕ API
# =============================================================================

def test_payment_api_example():
    """Пример тестирования Payment Bot API"""
    print("🧪 Тестирование Payment Bot API...")
    
    # Тест получения кошелька
    response = payment_client.get_payment_wallet("TTestUser123456789")
    print(f"✅ get_payment_wallet: {response}")
    
    # Тест проверки платежей
    response = payment_client.check_user_payments("TTestUser123456789")
    print(f"✅ check_user_payments: {response}")
    
    print("🎯 Тестирование завершено!")

# =============================================================================
# ПРИМЕР 8: ЛОГИРОВАНИЕ
# =============================================================================

import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def logged_payment_operation_example(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пример операции с логированием"""
    user_id = update.effective_user.id
    logger.info(f"Начало операции пополнения для пользователя {user_id}")
    
    try:
        # Получаем кошелек пользователя
        user_wallet = "TUserWallet123456789"  # В реальном коде из базы данных
        
        # Запрашиваем актуальный кошелек
        logger.info(f"Запрос актуального кошелька для {user_wallet}")
        response = payment_client.get_payment_wallet(user_wallet)
        
        if response.get('success'):
            active_wallet = response['wallet_address']
            logger.info(f"Получен актуальный кошелек: {active_wallet}")
            
            await update.message.reply_text(
                f"✅ **Кошелек получен!**\n\n"
                f"📱 Ваш кошелек: `{user_wallet}`\n"
                f"🏦 Активный кошелек: `{active_wallet}`"
            )
        else:
            error_msg = response.get('error', 'Неизвестная ошибка')
            logger.error(f"Ошибка получения кошелька: {error_msg}")
            await update.message.reply_text(f"❌ Ошибка: {error_msg}")
            
    except Exception as e:
        logger.error(f"Критическая ошибка в logged_payment_operation: {e}")
        await update.message.reply_text("❌ Произошла критическая ошибка")

# =============================================================================
# ЗАПУСК ТЕСТОВ
# =============================================================================

if __name__ == "__main__":
    print("🚀 Запуск примеров Payment Bot API...")
    test_payment_api_example()
    print("✅ Примеры готовы к использованию!")





