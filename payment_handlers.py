#!/usr/bin/env python3
"""
Обработчики платежей для бота ФондКлик
Интеграция с Payment Bot API
"""

import sqlite3
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from payment_client import payment_client

# Настройка логирования
logger = logging.getLogger(__name__)

# Путь к базе данных
DATABASE_PATH = "bot_database.db"

# =============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ
# =============================================================================

def get_user_wallet(user_id: int) -> str:
    """Получить кошелек пользователя из базы данных"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT wallet_address FROM user_wallets WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Ошибка получения кошелька пользователя {user_id}: {e}")
        return None

def save_user_wallet(user_id: int, wallet_address: str) -> bool:
    """Сохранить кошелек пользователя в базу данных"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_wallets (user_id, wallet_address, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, wallet_address))
            conn.commit()
            logger.info(f"Сохранен кошелек {wallet_address} для пользователя {user_id}")
            return True
    except Exception as e:
        logger.error(f"Ошибка сохранения кошелька для пользователя {user_id}: {e}")
        return False

def save_pending_payment(user_id: int, amount: float, wallet_address: str, payment_type: str = "deposit") -> int:
    """Сохранить ожидающий платеж в базу данных"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO pending_payments (user_id, amount, wallet_address, payment_type)
                VALUES (?, ?, ?, ?)
            ''', (user_id, amount, wallet_address, payment_type))
            payment_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Сохранен ожидающий платеж {payment_id} для пользователя {user_id}")
            return payment_id
    except Exception as e:
        logger.error(f"Ошибка сохранения ожидающего платежа: {e}")
        return 0

def get_pending_payments():
    """Получить все ожидающие платежи"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, amount, wallet_address, payment_type, created_at
                FROM pending_payments 
                WHERE status = 'pending'
                ORDER BY created_at ASC
            ''')
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Ошибка получения ожидающих платежей: {e}")
        return []

def mark_payment_confirmed(payment_id: int, tx_hash: str):
    """Отметить платеж как подтвержденный"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pending_payments 
                SET status = 'confirmed', tx_hash = ?
                WHERE id = ?
            ''', (tx_hash, payment_id))
            conn.commit()
            logger.info(f"Платеж {payment_id} подтвержден с хешем {tx_hash}")
    except Exception as e:
        logger.error(f"Ошибка обновления статуса платежа {payment_id}: {e}")

def add_user_balance(user_id: int, amount: float):
    """Добавить средства на баланс пользователя"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET balance = balance + ?, total_earned = total_earned + ?
                WHERE telegram_id = ?
            ''', (amount, amount, user_id))
            conn.commit()
            logger.info(f"Добавлено {amount} USDT на баланс пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка добавления баланса пользователю {user_id}: {e}")

# =============================================================================
# ОБРАБОТЧИКИ КОМАНД
# =============================================================================

async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /pay"""
    user_id = update.effective_user.id
    
    # Получаем сумму из аргументов команды
    if not context.args:
        await update.message.reply_text("❌ Укажите сумму для оплаты\nПример: /pay 100")
        return
    
    try:
        amount = float(context.args[0])
        if amount <= 0:
            await update.message.reply_text("❌ Сумма должна быть больше 0")
            return
    except ValueError:
        await update.message.reply_text("❌ Неверная сумма. Используйте числа.\nПример: /pay 100")
        return
    
    # Получаем кошелек пользователя
    user_wallet = get_user_wallet(user_id)
    
    if not user_wallet:
        await update.message.reply_text(
            "❌ У вас не настроен кошелек для оплаты\n\n"
            "Используйте команду /setwallet для настройки кошелька"
        )
        return
    
    # Создаем сообщение с адресом для оплаты
    payment_message = f"""
💳 **Оплата {amount} USDT**

🏦 **Адрес для оплаты:**
`{user_wallet}`

💰 **Сумма:** {amount} USDT
⏰ **Время на оплату:** 5 минут

📱 После оплаты нажмите кнопку "✅ Проверить оплату"
    """
    
    keyboard = [
        [InlineKeyboardButton("✅ Проверить оплату", callback_data=f"check_payment_{amount}")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_payment")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = await update.message.reply_text(
        payment_message, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )
    
    # Сохраняем информацию о платеже
    context.user_data['payment_amount'] = amount
    context.user_data['payment_wallet'] = user_wallet
    context.user_data['payment_message_id'] = message.message_id
    context.user_data['payment_time'] = datetime.now()
    
    # Сохраняем в базу данных
    payment_id = save_pending_payment(user_id, amount, user_wallet)
    context.user_data['payment_id'] = payment_id

async def setwallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для настройки кошелька пользователя"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "💳 **Настройка кошелька**\n\n"
            "Использование: /setwallet <адрес_кошелька>\n"
            "Пример: /setwallet TJR44gwdyGhLa4833zJtutNepRoNVFpMzX\n\n"
            "⚠️ Убедитесь, что это ваш кошелек TRC20!"
        )
        return
    
    wallet_address = context.args[0]
    
    # Проверяем валидность адреса (базовая проверка)
    if not wallet_address.startswith('T') or len(wallet_address) != 34:
        await update.message.reply_text(
            "❌ Неверный формат адреса TRC20 кошелька\n\n"
            "Адрес должен начинаться с 'T' и содержать 34 символа"
        )
        return
    
    # Сохраняем кошелек
    if save_user_wallet(user_id, wallet_address):
        await update.message.reply_text(
            f"✅ **Кошелек настроен!**\n\n"
            f"🏦 **Адрес:** `{wallet_address}`\n\n"
            f"Теперь вы можете использовать команду /pay для создания платежей",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Ошибка сохранения кошелька")

async def wallet_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для проверки баланса кошелька"""
    user_id = update.effective_user.id
    
    wallet = get_user_wallet(user_id)
    if not wallet:
        await update.message.reply_text(
            "❌ У вас не настроен кошелек\n\n"
            "Используйте команду /setwallet для настройки"
        )
        return
    
    # Получаем информацию о кошельке
    result = payment_client.get_wallet_info(wallet)
    
    if result.get("success"):
        balance = result.get("balance", 0)
        await update.message.reply_text(
            f"💰 **Баланс кошелька**\n\n"
            f"🏦 **Адрес:** `{wallet}`\n"
            f"💵 **Баланс:** {balance} USDT",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Ошибка получения баланса")

# =============================================================================
# ОБРАБОТЧИКИ CALLBACK QUERY
# =============================================================================

async def check_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки проверки платежа"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    amount = context.user_data.get('payment_amount')
    wallet = context.user_data.get('payment_wallet')
    
    if not amount or not wallet:
        await query.edit_message_text("❌ Информация о платеже не найдена")
        return
    
    # Проверяем, не истекло ли время
    payment_time = context.user_data.get('payment_time')
    if payment_time and datetime.now() - payment_time > timedelta(minutes=5):
        await query.edit_message_text("⏰ Время на оплату истекло")
        return
    
    # Показываем индикатор загрузки
    await query.edit_message_text("🔄 Проверяем платеж...")
    
    # Проверяем платеж через Payment Bot API
    result = payment_client.verify_payment(wallet, amount)
    
    if result.get("success") and result.get("confirmed"):
        # Платеж подтвержден
        tx_hash = result.get('tx_hash', 'N/A')
        
        success_message = f"""
✅ **Платеж подтвержден!**

💰 **Сумма:** {amount} USDT
🏦 **Кошелек:** `{wallet}`
🔗 **Хеш транзакции:** `{tx_hash}`

🎉 Спасибо за оплату!
        """
        
        keyboard = [
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            success_message, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
        
        # Обрабатываем успешный платеж
        await process_successful_payment(user_id, amount, tx_hash, context)
        
    else:
        # Платеж не найден
        error_message = f"""
❌ **Платеж не найден**

💰 **Ожидаемая сумма:** {amount} USDT
🏦 **Кошелек:** `{wallet}`

💡 **Возможные причины:**
• Платеж еще не поступил (подождите 1-2 минуты)
• Неверная сумма
• Платеж на другой кошелек

🔄 Попробуйте проверить еще раз через минуту
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить снова", callback_data=f"check_payment_{amount}")],
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel_payment")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            error_message, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )

async def cancel_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки отмены платежа"""
    query = update.callback_query
    await query.answer()
    
    # Очищаем данные о платеже
    context.user_data.pop('payment_amount', None)
    context.user_data.pop('payment_wallet', None)
    context.user_data.pop('payment_time', None)
    context.user_data.pop('payment_id', None)
    
    await query.edit_message_text("❌ Платеж отменен")

async def process_successful_payment(user_id: int, amount: float, tx_hash: str, context: ContextTypes.DEFAULT_TYPE):
    """Обработка успешного платежа"""
    try:
        # Добавляем средства на баланс пользователя
        add_user_balance(user_id, amount)
        
        # Отмечаем платеж как подтвержденный в базе данных
        payment_id = context.user_data.get('payment_id')
        if payment_id:
            mark_payment_confirmed(payment_id, tx_hash)
        
        # Очищаем данные о платеже
        context.user_data.pop('payment_amount', None)
        context.user_data.pop('payment_wallet', None)
        context.user_data.pop('payment_time', None)
        context.user_data.pop('payment_id', None)
        
        logger.info(f"Успешный платеж: пользователь {user_id}, сумма {amount} USDT, хеш {tx_hash}")
        
    except Exception as e:
        logger.error(f"Ошибка обработки успешного платежа: {e}")

# =============================================================================
# АВТОМАТИЧЕСКАЯ ПРОВЕРКА ПЛАТЕЖЕЙ
# =============================================================================

async def auto_check_payments():
    """Автоматическая проверка ожидающих платежей"""
    try:
        # Получаем все ожидающие платежи
        pending_payments = get_pending_payments()
        
        for payment in pending_payments:
            payment_id, user_id, amount, wallet, payment_type, created_at = payment
            
            # Проверяем платеж
            result = payment_client.verify_payment(wallet, amount)
            
            if result.get("success") and result.get("confirmed"):
                # Платеж подтвержден
                tx_hash = result.get('tx_hash', 'N/A')
                
                # Отмечаем как подтвержденный
                mark_payment_confirmed(payment_id, tx_hash)
                
                # Добавляем средства на баланс
                add_user_balance(user_id, amount)
                
                logger.info(f"Автоматически подтвержден платеж: пользователь {user_id}, сумма {amount} USDT")
                
    except Exception as e:
        logger.error(f"Ошибка автоматической проверки платежей: {e}")

# =============================================================================
# РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ
# =============================================================================

def register_payment_handlers(application):
    """Регистрация обработчиков платежей"""
    
    # Команды скрыты - доступны только через админ меню
    # application.add_handler(CommandHandler("pay", pay_command))
    # application.add_handler(CommandHandler("setwallet", setwallet_command))
    # application.add_handler(CommandHandler("walletbalance", wallet_balance_command))
    
    # Callback queries
    application.add_handler(CallbackQueryHandler(check_payment_callback, pattern="^check_payment_"))
    application.add_handler(CallbackQueryHandler(cancel_payment_callback, pattern="^cancel_payment$"))

def start_auto_payment_checker():
    """Запуск автоматической проверки платежей"""
    logger.info("💳 Платежная система интегрирована (автоматическая проверка отключена)")
    # Пока отключаем автоматическую проверку, чтобы избежать проблем с event loop
    # TODO: Добавить автоматическую проверку позже
