#!/bin/bash
# Скрипт для синхронизации активных кошельков из Payment Bot в Payment API

echo "🔄 Синхронизация кошельков..."

# Пути к базам данных
PAYMENT_BOT_DB="/opt/fondklik/payment_bot/payment_bot.db"
PAYMENT_API_DB="/opt/fondklik/payment_api/payments.db"

# Проверяем существование баз данных
if [ ! -f "$PAYMENT_BOT_DB" ]; then
    echo "❌ База данных Payment Bot не найдена: $PAYMENT_BOT_DB"
    exit 1
fi

if [ ! -f "$PAYMENT_API_DB" ]; then
    echo "⚠️ База данных Payment API не найдена, создаем..."
    mkdir -p /opt/fondklik/payment_api
    touch "$PAYMENT_API_DB"
fi

# Получаем активный кошелек из Payment Bot
ACTIVE_WALLET=$(sqlite3 "$PAYMENT_BOT_DB" "SELECT wallet_address FROM user_wallets WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1;" 2>/dev/null)

if [ -z "$ACTIVE_WALLET" ]; then
    echo "❌ Не найден активный кошелек в Payment Bot"
    exit 1
fi

echo "✅ Найден активный кошелек: $ACTIVE_WALLET"

# Создаем таблицу если её нет и вставляем/обновляем кошелек в Payment API
sqlite3 "$PAYMENT_API_DB" <<EOF
-- Создаем таблицу если её нет
CREATE TABLE IF NOT EXISTS user_wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    wallet_address TEXT,
    wallet_name TEXT,
    is_active BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, wallet_address)
);

-- Деактивируем все кошельки
UPDATE user_wallets SET is_active = 0;

-- Проверяем, существует ли кошелек
INSERT OR IGNORE INTO user_wallets (user_id, wallet_address, is_active, wallet_name)
VALUES (0, '$ACTIVE_WALLET', 1, 'Active Payment Wallet');

-- Активируем найденный кошелек
UPDATE user_wallets 
SET is_active = 1, created_at = CURRENT_TIMESTAMP
WHERE wallet_address = '$ACTIVE_WALLET';

-- Проверяем результат
SELECT wallet_address, is_active, created_at FROM user_wallets WHERE is_active = 1;
EOF

echo "✅ Синхронизация завершена!"

# Перезапускаем Payment API
echo "🔄 Перезапускаем Payment API..."
systemctl restart payment-api.service
sleep 2

echo "✅ Готово! Payment API перезапущен."

