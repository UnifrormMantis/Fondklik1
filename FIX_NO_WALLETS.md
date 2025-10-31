# ❌ ПРОБЛЕМА: Нет активных кошельков в Payment Bot

## 🔍 Причина:
API возвращает ошибку: **"Нет доступных активных кошельков"**

Это значит, что в Payment Bot нет кошельков или нет активного кошелька.

---

## ✅ РЕШЕНИЕ:

### ШАГ 1: Проверить статус Payment Bot

```bash
# Проверить статус Payment Bot
systemctl status payment-bot.service --no-pager -l | head -20
```

### ШАГ 2: Добавить кошелек в Payment Bot

**Способ 1: Через Telegram бот Payment Bot**

1. Откройте Payment Bot в Telegram
2. Нажмите "💳 Управление кошельками"
3. Нажмите "➕ Добавить кошелек"
4. Введите адрес кошелька (формат: `T...` - 34 символа)
5. После добавления нажмите на кошелек и выберите "🟢 Сделать активным"

**Способ 2: Через базу данных (если бот не работает)**

```bash
# Проверить кошельки в базе Payment Bot
sqlite3 /opt/fondklik/payment_bot/payment_bot.db "SELECT * FROM user_wallets WHERE user_id = 8489431460;" 2>/dev/null || echo "База не найдена"

# Или проверить где находится база
find /opt -name "*.db" -type f 2>/dev/null | grep -i payment
```

### ШАГ 3: Проверить что кошелек активный

```bash
# Найти базу данных Payment Bot
cd /opt/fondklik/payment_bot
find . -name "*.db" -type f

# Проверить кошельки (замените путь на реальный)
sqlite3 payment_bot.db "SELECT user_id, wallet_address, is_active FROM user_wallets;"

# Если нет активного - установить активный (замените wallet_id на реальный ID)
sqlite3 payment_bot.db "UPDATE user_wallets SET is_active = 1 WHERE wallet_id = 1;"
```

### ШАГ 4: Перезапустить Payment Bot

```bash
systemctl restart payment-bot.service
sleep 3
systemctl status payment-bot.service --no-pager -l | head -15
```

### ШАГ 5: Проверить API снова

```bash
# Проверить что API теперь возвращает кошелек
curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: QGCHTq8vAjaeeSAXdzkH2OQMmyzfirvVKOxxxivNzyc" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test"}' | python3 -m json.tool
```

---

## 🎯 БЫСТРОЕ РЕШЕНИЕ:

**Если у вас есть адрес кошелька для добавления:**

1. Откройте Payment Bot в Telegram (второй бот)
2. Добавьте кошелек через интерфейс
3. Активируйте его
4. Проверьте API снова

---

**Выполните проверку и добавьте кошелек!**

