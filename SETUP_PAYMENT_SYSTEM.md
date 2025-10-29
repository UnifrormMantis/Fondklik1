# 🔧 Настройка собственной платежной системы

## 📋 Что нужно сделать

### 1. Указать URL вашей платежной системы

Отредактируйте файл `payment_config.py`:

```python
# Замените на реальный URL вашей платежной системы
PAYMENT_SYSTEM_URL = "https://your-real-payment-system.com"
```

### 2. Проверить API ключ

Убедитесь, что API ключ правильный в файле `payment_config.py`:

```python
CUSTOM_PAYMENT_API_KEY = "tO8RcgkEg3ie8CsGWni00d3YHGxjlr5ce6KNykJBbT0"
```

### 3. Настроить API endpoints

Убедитесь, что ваша платежная система поддерживает следующие endpoints:

#### Создание платежа
```
POST /api/v1/payments/create
```

**Запрос:**
```json
{
  "amount": 10.0,
  "currency": "USDT",
  "description": "Пополнение баланса на 10.0 USDT",
  "user_id": 12345,
  "callback_url": "https://your-payment-system.com/api/v1/payments/callback",
  "success_url": "https://t.me/your_bot_username",
  "fail_url": "https://t.me/your_bot_username"
}
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "payment_id": "unique_payment_id",
    "payment_url": "https://your-payment-system.com/pay/...",
    "amount": 10.0,
    "currency": "USDT",
    "status": "pending"
  }
}
```

#### Проверка статуса платежа
```
GET /api/v1/payments/{payment_id}/status
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "payment_id": "unique_payment_id",
    "status": "paid",  // "pending", "paid", "failed", "cancelled", "expired"
    "amount": 10.0,
    "currency": "USDT"
  }
}
```

### 4. Настроить аутентификацию

Ваша система должна поддерживать аутентификацию через:

- **API Key**: `X-API-Key` заголовок
- **Подпись**: `X-Signature` заголовок (HMAC-SHA256)
- **Временная метка**: `X-Timestamp` заголовок

### 5. Настроить webhook (опционально)

Для мгновенных уведомлений о платежах:

```
POST /api/v1/payments/callback
```

**Webhook payload:**
```json
{
  "signature": "hmac_signature",
  "data": {
    "payment_id": "unique_payment_id",
    "status": "paid",
    "amount": 10.0,
    "currency": "USDT",
    "user_id": 12345
  }
}
```

## 🧪 Тестирование

### 1. Проверьте подключение
```bash
python3 test_custom_payment.py
```

### 2. Проверьте бота
```bash
# Остановите текущий бот
./manage_bot.sh 5

# Запустите с новой платежной системой
./manage_bot.sh 1
```

## 🔧 Настройка полей ответа

Если ваша платежная система возвращает другие названия полей, обновите файл `custom_payment_api.py`:

### В методе `create_payment`:
```python
# Замените на ваши поля
payment_id = payment_data.get('payment_id') or payment_data.get('id') or payment_data.get('transaction_id')
payment_url = payment_data.get('payment_url') or payment_data.get('pay_url') or payment_data.get('url')
```

### В методе `check_payment_status`:
```python
# Замените на ваши статусы
status_map = {
    "completed": "paid",
    "success": "paid", 
    "pending": "pending",
    "failed": "failed",
    "cancelled": "failed",
    "expired": "failed"
}
```

## 🚨 Устранение проблем

### Ошибка подключения
```
Cannot connect to host api.your-payment-system.com:443
```
**Решение:** Проверьте URL в `payment_config.py`

### Ошибка аутентификации
```
HTTP 401 Unauthorized
```
**Решение:** Проверьте API ключ и настройки подписи

### Неправильный формат ответа
```
KeyError: 'payment_id'
```
**Решение:** Обновите маппинг полей в `custom_payment_api.py`

## 📞 Поддержка

Если у вас есть вопросы по интеграции:

1. Проверьте логи: `./manage_bot.sh 7`
2. Запустите тест: `python3 test_custom_payment.py`
3. Проверьте конфигурацию: `payment_config.py`

## 🎯 Следующие шаги

1. ✅ Указать правильный URL платежной системы
2. ✅ Проверить API endpoints
3. ✅ Настроить аутентификацию
4. ✅ Протестировать интеграцию
5. ✅ Запустить бота с новой системой











