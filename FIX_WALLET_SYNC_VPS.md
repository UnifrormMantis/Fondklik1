# ✅ ИСПРАВЛЕНИЕ СИНХРОНИЗАЦИИ КОШЕЛЬКОВ

## ❗ ПРОБЛЕМА:
API ищет активный кошелек в своей базе `payments.db`, но там может не быть кошельков из Payment Bot

---

## 📋 РЕШЕНИЕ НА VPS:

### Вариант 1: Использовать скрипт синхронизации

```bash
# 1. Скачать скрипт на VPS (выполните на своей машине):
# scp /Users/roma/Desktop/Fondklik/sync_wallets_to_api.sh root@199.217.98.13:/opt/fondklik/

# 2. На VPS выполнить:
cd /opt/fondklik
chmod +x sync_wallets_to_api.sh
./sync_wallets_to_api.sh
```

### Вариант 2: Вручную скопировать кошелек

```bash
# 1. Найти активный кошелек в Payment Bot
cd /opt/fondklik/payment_bot
ACTIVE_WALLET=$(sqlite3 payment_bot.db "SELECT wallet_address FROM user_wallets WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1;")
echo "Активный кошелек: $ACTIVE_WALLET"

# 2. Скопировать в базу Payment API
cd /opt/fondklik/payment_api
sqlite3 payments.db <<EOF
CREATE TABLE IF NOT EXISTS user_wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    wallet_address TEXT,
    wallet_name TEXT,
    is_active BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, wallet_address)
);

UPDATE user_wallets SET is_active = 0;

INSERT OR REPLACE INTO user_wallets (user_id, wallet_address, is_active, wallet_name)
VALUES (0, '$ACTIVE_WALLET', 1, 'Active Payment Wallet');

SELECT wallet_address, is_active FROM user_wallets WHERE is_active = 1;
EOF

# 3. Перезапустить Payment API
systemctl restart payment-api.service
sleep 2
systemctl status payment-api.service --no-pager -l | head -15
```

---

## ✅ ПРОВЕРКА:

```bash
# Проверить, что API видит кошелек
curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: QGCHTq8vAjaeeSAXdzkH2OQMmyzfirvVKOxxxivNzyc" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test"}' | jq .
```

**После синхронизации бот должен показывать реальный активный кошелек!**

