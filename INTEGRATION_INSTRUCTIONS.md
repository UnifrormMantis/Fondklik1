# 🔗 Инструкция по интеграции Payment Bot в основной бот

## 📋 Обзор

Этот документ содержит пошаговую инструкцию для интеграции Payment Bot в ваш основной Telegram бот. Payment Bot предоставляет API для обработки TRC20 платежей с автоматическим подтверждением.

## 🎯 Что получите после интеграции

- ✅ Автоматическое подтверждение TRC20 платежей
- ✅ Проверка платежей по кошелькам пользователей
- ✅ API для создания и проверки платежей
- ✅ Система уведомлений о транзакциях
- ✅ Управление кошельками пользователей

## 🚀 Шаг 1: Подготовка Payment Bot

### 1.1 Запуск Payment Bot
```bash
# В директории Payment Bot
./start_bot.sh
```

### 1.2 Запуск API сервера
```bash
# Запуск Simple Payment API
./start_simple_api.sh
```

### 1.3 Получение API ключа
```bash
curl -s http://localhost:8002/get-api-key
```

**Ваш API ключ:** `X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco`

## 🔧 Шаг 2: Настройка основного бота

### 2.1 Добавьте в config.py основного бота:

```python
# config.py
# ... существующие настройки ...

# Payment Bot Integration
PAYMENT_API_URL = "http://localhost:8002"
PAYMENT_API_KEY = "X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco"

# Настройки для интеграции
PAYMENT_BOT_ENABLED = True
PAYMENT_TIMEOUT = 300  # 5 минут на оплату
```

### 2.2 Создайте файл payment_client.py в основном боте:

```python
# payment_client.py
import requests
import logging
from typing import Dict, Optional, Any
import config

logger = logging.getLogger(__name__)

class PaymentClient:
    def __init__(self):
        self.api_url = config.PAYMENT_API_URL
        self.api_key = config.PAYMENT_API_KEY
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def verify_payment(self, wallet_address: str, amount: float, currency: str = "USDT") -> Dict[str, Any]:
        """Проверить платеж на кошелек"""
        try:
            response = requests.post(
                f"{self.api_url}/verify-payment",
                headers=self.headers,
                json={
                    "wallet_address": wallet_address,
                    "amount": amount,
                    "currency": currency
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка проверки платежа: {response.status_code} - {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Payment API: {e}")
            return {"success": False, "error": str(e)}
    
    def get_wallet_info(self, wallet_address: str) -> Dict[str, Any]:
        """Получить информацию о кошельке"""
        try:
            response = requests.get(
                f"{self.api_url}/wallet-info",
                headers=self.headers,
                params={"wallet_address": wallet_address},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения информации о кошельке: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Payment API: {e}")
            return {"success": False, "error": str(e)}
    
    def check_payment_status(self, wallet_address: str, amount: float) -> bool:
        """Проверить статус платежа (упрощенная версия)"""
        result = self.verify_payment(wallet_address, amount)
        return result.get("success", False) and result.get("confirmed", False)

# Глобальный экземпляр клиента
payment_client = PaymentClient()
```

## 🎮 Шаг 3: Интеграция в основной бот

### 3.1 Добавьте обработчик команды оплаты:

```python
# main_bot.py
from payment_client import payment_client
import asyncio
from datetime import datetime, timedelta

async def payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /pay"""
    user_id = update.effective_user.id
    
    # Получаем сумму из аргументов команды
    if not context.args:
        await update.message.reply_text("❌ Укажите сумму для оплаты\nПример: /pay 100")
        return
    
    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверная сумма. Используйте числа.\nПример: /pay 100")
        return
    
    # Получаем кошелек пользователя (из вашей базы данных)
    user_wallet = get_user_wallet(user_id)  # Ваша функция для получения кошелька
    
    if not user_wallet:
        await update.message.reply_text("❌ У вас не настроен кошелек для оплаты")
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
    
    # Сохраняем информацию о платеже для последующей проверки
    context.user_data['payment_amount'] = amount
    context.user_data['payment_wallet'] = user_wallet
    context.user_data['payment_message_id'] = message.message_id
    context.user_data['payment_time'] = datetime.now()
```

### 3.2 Добавьте обработчик проверки платежа:

```python
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
        success_message = f"""
✅ **Платеж подтвержден!**

💰 **Сумма:** {amount} USDT
🏦 **Кошелек:** `{wallet}`
🔗 **Хеш транзакции:** `{result.get('tx_hash', 'N/A')}`

🎉 Спасибо за оплату!
        """
        
        keyboard = [
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            success_message, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
        
        # Здесь добавьте логику зачисления средств пользователю
        await process_successful_payment(user_id, amount, result.get('tx_hash'))
        
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

async def process_successful_payment(user_id: int, amount: float, tx_hash: str):
    """Обработка успешного платежа"""
    # Здесь добавьте вашу логику:
    # - Зачисление средств на баланс пользователя
    # - Обновление базы данных
    # - Отправка уведомлений
    # - Логирование транзакции
    
    logger.info(f"Успешный платеж: пользователь {user_id}, сумма {amount} USDT, хеш {tx_hash}")
    
    # Пример:
    # add_user_balance(user_id, amount)
    # log_transaction(user_id, amount, tx_hash, "payment_received")
```

### 3.3 Зарегистрируйте обработчики:

```python
# В функции main() или где регистрируете обработчики
def main():
    # ... существующие обработчики ...
    
    # Обработчики платежей
    application.add_handler(CommandHandler("pay", payment_command))
    application.add_handler(CallbackQueryHandler(check_payment_callback, pattern="^check_payment_"))
    application.add_handler(CallbackQueryHandler(cancel_payment_callback, pattern="^cancel_payment$"))
    
    # ... остальной код ...
```

## 🔄 Шаг 4: Автоматическая проверка платежей (опционально)

### 4.1 Добавьте фоновую задачу для автоматической проверки:

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def auto_check_payments():
    """Автоматическая проверка ожидающих платежей"""
    # Получаем все ожидающие платежи из вашей базы данных
    pending_payments = get_pending_payments()  # Ваша функция
    
    for payment in pending_payments:
        user_id = payment['user_id']
        amount = payment['amount']
        wallet = payment['wallet']
        
        # Проверяем платеж
        result = payment_client.verify_payment(wallet, amount)
        
        if result.get("success") and result.get("confirmed"):
            # Платеж подтвержден - уведомляем пользователя
            await notify_payment_confirmed(user_id, amount, result.get('tx_hash'))
            # Обновляем статус в базе данных
            mark_payment_confirmed(payment['id'])

# Запуск планировщика
scheduler = AsyncIOScheduler()
scheduler.add_job(auto_check_payments, 'interval', minutes=1)
scheduler.start()
```

## 🛠️ Шаг 5: Дополнительные функции

### 5.1 Команда для настройки кошелька:

```python
async def set_wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для настройки кошелька пользователя"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "💳 **Настройка кошелька**\n\n"
            "Использование: /setwallet <адрес_кошелька>\n"
            "Пример: /setwallet TJR44gwdyGhLa4833zJtutNepRoNVFpMzX"
        )
        return
    
    wallet_address = context.args[0]
    
    # Проверяем валидность адреса (базовая проверка)
    if not wallet_address.startswith('T') or len(wallet_address) != 34:
        await update.message.reply_text("❌ Неверный формат адреса TRC20 кошелька")
        return
    
    # Сохраняем кошелек в базу данных
    save_user_wallet(user_id, wallet_address)  # Ваша функция
    
    await update.message.reply_text(
        f"✅ **Кошелек настроен!**\n\n"
        f"🏦 **Адрес:** `{wallet_address}`\n\n"
        f"Теперь вы можете использовать команду /pay для создания платежей",
        parse_mode='Markdown'
    )
```

### 5.2 Команда для проверки баланса кошелька:

```python
async def wallet_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для проверки баланса кошелька"""
    user_id = update.effective_user.id
    
    wallet = get_user_wallet(user_id)  # Ваша функция
    if not wallet:
        await update.message.reply_text("❌ У вас не настроен кошелек")
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
```

## 📦 Шаг 6: Установка зависимостей

Добавьте в requirements.txt основного бота:

```txt
requests>=2.28.0
apscheduler>=3.9.0
```

## 🔧 Шаг 7: Настройка базы данных

Добавьте таблицы для хранения информации о платежах:

```sql
-- Таблица для хранения кошельков пользователей
CREATE TABLE user_wallets (
    user_id INTEGER PRIMARY KEY,
    wallet_address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения ожидающих платежей
CREATE TABLE pending_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    wallet_address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    tx_hash TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
```

## 🚨 Важные замечания

1. **Безопасность**: Никогда не храните API ключи в коде. Используйте переменные окружения или конфигурационные файлы.

2. **Обработка ошибок**: Всегда обрабатывайте ошибки при работе с API.

3. **Таймауты**: Устанавливайте разумные таймауты для API запросов.

4. **Логирование**: Ведите подробные логи всех платежных операций.

5. **Тестирование**: Тщательно тестируйте интеграцию на тестовых кошельках.

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи Payment Bot
2. Убедитесь, что API сервер запущен
3. Проверьте правильность API ключа
4. Проверьте сетевое соединение между ботами

---

**Удачной интеграции! 🚀**
