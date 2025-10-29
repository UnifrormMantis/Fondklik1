# 🔧 ИНСТРУКЦИЯ ДЛЯ НАСТРОЙКИ PAYMENT BOT

## 📋 Что нужно реализовать в Payment Bot

### 1. **Эндпоинт `/get-payment-wallet`**
**Метод:** POST  
**Описание:** Получить активный кошелек для приема платежей, передав кошелек пользователя

**Запрос:**
```json
{
  "user_wallet": "T... (кошелек пользователя)"
}
```

**Ответ:**
```json
{
  "success": true,
  "wallet_address": "T... (активный кошелек для приема платежей)"
}
```

**Логика:**
- Принимает кошелек пользователя
- Возвращает активный кошелек для приема платежей
- Запоминает связь: пользователь → активный кошелек

---

### 2. **Эндпоинт `/check-user-payments`**
**Метод:** POST  
**Описание:** Проверить переводы с кошелька пользователя на активный кошелек

**Запрос:**
```json
{
  "user_wallet": "T... (кошелек пользователя)"
}
```

**Ответ:**
```json
{
  "success": true,
  "payments": [
    {
      "amount": 100.0,
      "tx_hash": "0x...",
      "confirmed": true,
      "timestamp": "2025-10-07T23:00:00Z"
    }
  ]
}
```

**Логика:**
- Находит активный кошелек для данного пользователя
- Проверяет блокчейн на наличие переводов с `user_wallet` на активный кошелек
- Возвращает список подтвержденных переводов
- Сортирует по времени (новые первыми)

---

## 🔄 Алгоритм работы

### **Шаг 1: Пользователь создает депозит**
1. Пользователь вводит свой кошелек в боте
2. Бот вызывает `/get-payment-wallet` с кошельком пользователя
3. Payment Bot возвращает активный кошелек для приема платежей
4. Бот показывает пользователю активный кошелек для перевода

### **Шаг 2: Пользователь переводит деньги**
1. Пользователь переводит USDT с своего кошелька на активный кошелек
2. Payment Bot отслеживает блокчейн в реальном времени

### **Шаг 3: Проверка платежа**
1. Пользователь нажимает "✅ Проверить платеж"
2. Бот вызывает `/check-user-payments` с кошельком пользователя
3. Payment Bot проверяет переводы с кошелька пользователя на активный кошелек
4. Возвращает информацию о подтвержденных переводах

### **Шаг 4: Создание депозита**
1. Бот получает сумму и хеш транзакции
2. Создает депозит в базе данных
3. Уведомляет пользователя об успехе

---

## 🗄️ Структура данных в Payment Bot

### **Таблица связей пользователей:**
```sql
CREATE TABLE user_payment_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_wallet TEXT NOT NULL,
    active_wallet TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_wallet)
);
```

### **Таблица отслеживания платежей:**
```sql
CREATE TABLE payment_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_wallet TEXT NOT NULL,
    active_wallet TEXT NOT NULL,
    amount REAL NOT NULL,
    tx_hash TEXT NOT NULL,
    confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚙️ Настройки API

### **Базовый URL:** `http://localhost:8002`

### **Заголовки:**
```
X-API-Key: X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco
Content-Type: application/json
```

---

## 🧪 Тестирование

### **Тест 1: Получение кошелька для платежа**
```bash
curl -X POST http://localhost:8002/get-payment-wallet \
  -H "X-API-Key: X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "TTestUserWallet123456789"}'
```

### **Тест 2: Проверка платежей пользователя**
```bash
curl -X POST http://localhost:8002/check-user-payments \
  -H "X-API-Key: X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "TTestUserWallet123456789"}'
```

---

## 🚨 Важные моменты

1. **Безопасность:** Всегда проверяйте API ключ
2. **Таймауты:** Устанавливайте таймауты 10 секунд для запросов
3. **Логирование:** Логируйте все запросы и ответы
4. **Обработка ошибок:** Возвращайте понятные сообщения об ошибках
5. **Подтверждения:** Проверяйте количество подтверждений в блокчейне (минимум 1)

---

## 📞 Поддержка

При возникновении проблем проверьте:
- Запущен ли Payment Bot
- Правильный ли API ключ
- Доступен ли эндпоинт
- Корректные ли данные в запросе






