# 🔧 ИСПРАВЛЕНИЕ СИНХРОНИЗАЦИИ КОШЕЛЬКОВ

## ❗ ПРОБЛЕМА:

Согласно `UPDATED_INTEGRATION_INSTRUCTIONS.md`, эндпоинт `/get-payment-wallet` должен возвращать активный кошелек из базы данных Payment API. 

**Ошибка:** "Нет доступных активных кошельков" - значит в базе Payment API нет активных кошельков.

---

## ✅ РЕШЕНИЕ:

### ШАГ 1: Найти базы данных

Выполните на VPS:

```bash
# 1. Найти базу Payment API
find /opt/fondklik/payment_api -name "*.db" -type f

# 2. Найти базу Payment Bot
find /opt/fondklik/payment_bot -name "*.db" -type f

# 3. Проверить активный кошелек в Payment Bot
DB_BOT=$(find /opt/fondklik/payment_bot -name "*.db" -type f | head -1)
if [ ! -z "$DB_BOT" ]; then
    echo "База Payment Bot: $DB_BOT"
    sqlite3 "$DB_BOT" "SELECT wallet_address, is_active FROM user_wallets WHERE is_active = 1 LIMIT 1;"
fi
```

### ШАГ 2: Добавить кошелек в базу Payment API

```bash
# 1. Получить активный кошелек из Payment Bot
DB_BOT=$(find /opt/fondklik/payment_bot -name "*.db" -type f | head -1)
WALLET=$(sqlite3 "$DB_BOT" "SELECT wallet_address FROM user_wallets WHERE is_active = 1 LIMIT 1;" 2>/dev/null)

if [ -z "$WALLET" ]; then
    echo "❌ Активный кошелек не найден в Payment Bot"
    echo "Добавьте кошелек через Telegram бот Payment Bot или укажите вручную:"
    echo "WALLET='TYourWalletAddress12345678901234567890'"
    exit 1
fi

echo "✅ Найден активный кошелек: $WALLET"

# 2. Найти базу Payment API
DB_API=$(find /opt/fondklik/payment_api -name "*.db" -type f | head -1)
if [ -z "$DB_API" ]; then
    echo "❌ База Payment API не найдена"
    echo "Ищем в рабочей директории..."
    DB_API="/opt/fondklik/payment_api/payments.db"
    if [ ! -f "$DB_API" ]; then
        echo "Создаем новую базу..."
        touch "$DB_API"
    fi
fi

echo "База Payment API: $DB_API"

# 3. Создать таблицу user_wallets если нет
sqlite3 "$DB_API" "CREATE TABLE IF NOT EXISTS user_wallets (
    user_id INTEGER,
    wallet_address TEXT PRIMARY KEY,
    is_active INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"

# 4. Добавить кошелек в Payment API
sqlite3 "$DB_API" "INSERT OR REPLACE INTO user_wallets (user_id, wallet_address, is_active) VALUES (8489431460, '$WALLET', 1);"

# 5. Проверить что добавлено
echo ""
echo "✅ Кошельки в Payment API:"
sqlite3 "$DB_API" "SELECT wallet_address, is_active FROM user_wallets;"
```

### ШАГ 3: Перезапустить Payment API

```bash
systemctl restart payment-api.service
sleep 3
systemctl status payment-api.service --no-pager -l | head -15
```

### ШАГ 4: Проверить API

```bash
# Получить API ключ если нужно
API_KEY=$(cat /opt/fondklik/bot/.env | grep PAYMENT_API_KEY | cut -d'=' -f2)

# Тест получения кошелька
curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test"}' | python3 -m json.tool
```

**Теперь должно вернуть кошелек, а не ошибку!**

---

## 🔄 АВТОМАТИЗАЦИЯ: Скрипт синхронизации

Создайте скрипт для автоматической синхронизации:

```bash
#!/bin/bash
# sync_wallets.sh

DB_BOT=$(find /opt/fondklik/payment_bot -name "*.db" -type f | head -1)
DB_API=$(find /opt/fondklik/payment_api -name "*.db" -type f | head -1)

if [ -z "$DB_BOT" ] || [ -z "$DB_API" ]; then
    echo "❌ Базы данных не найдены"
    exit 1
fi

# Получить активный кошелек из Payment Bot
WALLET=$(sqlite3 "$DB_BOT" "SELECT wallet_address FROM user_wallets WHERE is_active = 1 LIMIT 1;" 2>/dev/null)

if [ ! -z "$WALLET" ]; then
    # Синхронизировать с Payment API
    sqlite3 "$DB_API" "CREATE TABLE IF NOT EXISTS user_wallets (user_id INTEGER, wallet_address TEXT PRIMARY KEY, is_active INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
    sqlite3 "$DB_API" "INSERT OR REPLACE INTO user_wallets (user_id, wallet_address, is_active) VALUES (8489431460, '$WALLET', 1);"
    echo "✅ Кошелек синхронизирован: $WALLET"
else
    echo "⚠️ Активный кошелек не найден в Payment Bot"
fi
```

---

**Выполните команды из ШАГ 2 для синхронизации кошельков!**

