# 🔄 Синхронизация кошельков между Payment Bot и Payment API

## ❗ ПРОБЛЕМА:

Payment API ищет кошельки в **своей базе данных**, а не в базе Payment Bot.  
Базы данных не синхронизированы!

---

## ✅ РЕШЕНИЕ: Добавить кошелек в базу Payment API

Выполните на VPS:

```bash
# 1. Найти базу данных Payment API
find /opt/fondklik/payment_api -name "*.db" -type f

# 2. Проверить структуру базы Payment API
DB_API=$(find /opt/fondklik/payment_api -name "*.db" -type f | head -1)
echo "База Payment API: $DB_API"

sqlite3 "$DB_API" ".tables"
sqlite3 "$DB_API" ".schema user_wallets" 2>/dev/null || echo "Таблица user_wallets не найдена"

# 3. Проверить какие кошельки есть в Payment API
sqlite3 "$DB_API" "SELECT * FROM user_wallets;" 2>/dev/null || echo "Таблица пуста или не существует"

# 4. Найти базу Payment Bot чтобы получить кошелек
DB_BOT=$(find /opt/fondklik/payment_bot -name "*.db" -type f | head -1)
echo "База Payment Bot: $DB_BOT"

# 5. Получить активный кошелек из Payment Bot
if [ ! -z "$DB_BOT" ]; then
    WALLET=$(sqlite3 "$DB_BOT" "SELECT wallet_address FROM user_wallets WHERE is_active = 1 LIMIT 1;" 2>/dev/null)
    echo "Активный кошелек в Payment Bot: $WALLET"
    
    # 6. Добавить кошелек в базу Payment API
    if [ ! -z "$WALLET" ] && [ ! -z "$DB_API" ]; then
        sqlite3 "$DB_API" "INSERT OR IGNORE INTO user_wallets (user_id, wallet_address, is_active) VALUES (8489431460, '$WALLET', 1);"
        echo "✅ Кошелек добавлен в Payment API"
        
        # 7. Проверить что добавлено
        sqlite3 "$DB_API" "SELECT * FROM user_wallets;"
    fi
else
    echo "❌ База Payment Bot не найдена"
fi
```

---

## 🔄 АЛЬТЕРНАТИВНО: Добавить кошелек вручную

Если знаете адрес кошелька:

```bash
# Замените WALLET_ADDRESS на реальный адрес
WALLET_ADDRESS="TWALLET_ADDRESS_HERE"
DB_API=$(find /opt/fondklik/payment_api -name "*.db" -type f | head -1)

# Создать таблицу если нет
sqlite3 "$DB_API" "CREATE TABLE IF NOT EXISTS user_wallets (
    user_id INTEGER,
    wallet_address TEXT PRIMARY KEY,
    is_active INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"

# Добавить кошелек
sqlite3 "$DB_API" "INSERT OR REPLACE INTO user_wallets (user_id, wallet_address, is_active) VALUES (8489431460, '$WALLET_ADDRESS', 1);"

# Проверить
sqlite3 "$DB_API" "SELECT * FROM user_wallets;"
```

---

## 🧪 ПРОВЕРКА:

После добавления кошелька:

```bash
# Тест API
curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: QGCHTq8vAjaeeSAXdzkH2OQMmyzfirvVKOxxxivNzyc" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test"}' | python3 -m json.tool
```

**Должен вернуть кошелек, а не ошибку!**

---

**Выполните команды синхронизации!**

