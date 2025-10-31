# 🔍 Проверка кошельков в Payment Bot

## ❗ ПРОБЛЕМА:
Payment API работает, но не может найти активные кошельки в Payment Bot.

---

## 📋 ВЫПОЛНИТЕ НА VPS:

```bash
# 1. Проверить статус Payment API
systemctl status payment-api.service --no-pager -l | head -20

# 2. Проверить статус Payment Bot (второй бот)
systemctl status payment-bot.service --no-pager -l | head -20

# 3. Найти базы данных Payment Bot
find /opt -name "*.db" -type f 2>/dev/null

# 4. Проверить структуру Payment Bot директории
ls -la /opt/fondklik/payment_bot/ 2>/dev/null || ls -la /opt/fondklik/платежка/ 2>/dev/null

# 5. Найти базу данных с кошельками
find /opt -name "payment_bot.db" -o -name "payments.db" -o -name "*.db" | grep -i payment

# 6. Проверить логи Payment Bot (если есть)
journalctl -u payment-bot.service -n 30 --no-pager 2>/dev/null || echo "Сервис payment-bot не найден"
```

---

## 🎯 ГДЕ НАХОДИТСЯ PAYMENT BOT:

Payment Bot (второй бот) должен быть установлен в:
- `/opt/fondklik/payment_bot/` или
- `/opt/fondklik/платежка/`

База данных Payment Bot обычно:
- `payment_bot.db` или
- `payments.db`

---

## ✅ ДОБАВИТЬ КОШЕЛЕК:

### Через Telegram бот Payment Bot:
1. Откройте Payment Bot в Telegram
2. Нажмите "💳 Управление кошельками"
3. Нажмите "➕ Добавить кошелек"
4. Введите адрес: `T...` (34 символа)
5. Активируйте кошелек

### Через базу данных (если бот не работает):
```bash
# Найти базу
DB_PATH=$(find /opt -name "payment_bot.db" -o -name "payments.db" | head -1)
echo "База: $DB_PATH"

# Проверить структуру таблицы
sqlite3 "$DB_PATH" ".tables"
sqlite3 "$DB_PATH" ".schema user_wallets" 2>/dev/null || sqlite3 "$DB_PATH" ".schema wallets"

# Добавить кошелек (замените WALLET_ADDRESS на реальный адрес)
# sqlite3 "$DB_PATH" "INSERT INTO user_wallets (user_id, wallet_address, is_active) VALUES (8489431460, 'TWALLET_ADDRESS_HERE', 1);"
```

---

**Выполните команды проверки и найдите базу данных Payment Bot!**

