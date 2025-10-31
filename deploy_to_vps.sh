#!/bin/bash

# === ПОЛНЫЙ СКРИПТ ДЕПЛОЯ НА VPS ===
# Выполните этот скрипт на VPS после подключения по SSH

echo "=========================================="
echo "🚀 ДЕПЛОЙ ВСЕХ СЕРВИСОВ НА VPS"
echo "=========================================="
echo ""

# 1. Обновление Fondklik Bot
echo "📦 1. Обновление Fondklik Bot..."
cd /opt/fondklik/bot || exit 1
git pull origin main || echo "⚠️  Git pull не удался, пропускаем"
echo "✅ Fondklik Bot обновлен"
echo ""

# 2. Обновление Payment Bot
echo "📦 2. Обновление Payment Bot..."
cd /opt/fondklik/payment_bot || exit 1
git pull origin main || echo "⚠️  Git pull не удался, пропускаем"
echo "✅ Payment Bot обновлен"
echo ""

# 3. Обновление Payment API
echo "📦 3. Обновление Payment API..."
cd /opt/fondklik/payment_api || exit 1
# Если используется git, раскомментируйте:
# git pull origin main || echo "⚠️  Git pull не удался"
echo "✅ Payment API готов"
echo ""

# 4. Обновление конфигурации Fondklik Bot
echo "⚙️  4. Обновление конфигурации..."
cd /opt/fondklik/bot
if ! grep -q "PAYMENT_API_KEY" .env 2>/dev/null; then
    echo "PAYMENT_API_KEY=QGCHTq8vAjaeeSAXdzkH2OQMmyzfirvVKOxxxivNzyc" >> .env
    echo "PAYMENT_API_URL=http://127.0.0.1:8001" >> .env
    echo "✅ .env обновлен"
else
    echo "⚠️  .env уже содержит PAYMENT_API_KEY"
fi
echo ""

# 5. Обновление баз данных
echo "💾 5. Обновление баз данных..."

# 5.1 Fondklik Bot - админ
echo "  5.1. Fondklik Bot - добавление админа..."
cd /opt/fondklik/bot
sqlite3 bot_database.db << 'SQL'
INSERT OR REPLACE INTO admins (telegram_id, username, first_name, last_name)
VALUES (8489431460, 'мартин', 'Мартин', NULL);
SQL
echo "    ✅ Админ добавлен в Fondklik Bot"

# 5.2 Payment Bot - whitelist и api_keys
echo "  5.2. Payment Bot - обновление базы..."
cd /opt/fondklik/payment_bot
sqlite3 payments.db << 'SQL'
INSERT OR REPLACE INTO users (user_id, username)
VALUES (8489431460, 'мартин');

CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    api_key TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO api_keys (api_key, is_active)
VALUES ('QGCHTq8vAjaeeSAXdzkH2OQMmyzfirvVKOxxxivNzyc', 1);
SQL
echo "    ✅ База Payment Bot обновлена"

# 5.3 Payment API - api_keys
echo "  5.3. Payment API - создание таблицы api_keys..."
cd /opt/fondklik/payment_api
sqlite3 payments.db << 'SQL' 2>/dev/null || sqlite3 payment_api.db << 'SQL'
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    api_key TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO api_keys (api_key, is_active)
VALUES ('QGCHTq8vAjaeeSAXdzkH2OQMmyzfirvVKOxxxivNzyc', 1);
SQL
echo "    ✅ База Payment API обновлена"
echo ""

# 6. Перезапуск сервисов
echo "🔄 6. Перезапуск сервисов..."
systemctl daemon-reload
sleep 1

echo "  6.1. Перезапуск Payment API..."
systemctl restart payment-api.service
sleep 2

echo "  6.2. Перезапуск Fondklik Bot..."
systemctl restart fondklik-bot.service
sleep 2

echo "  6.3. Перезапуск Payment Bot..."
systemctl restart payment-bot.service
sleep 2

echo ""

# 7. Проверка статуса
echo "=========================================="
echo "📊 ПРОВЕРКА СТАТУСА СЕРВИСОВ"
echo "=========================================="
echo ""

echo "📡 Payment API:"
systemctl is-active payment-api.service && echo "  ✅ Работает" || echo "  ❌ Остановлен"
curl -s http://localhost:8001/health >/dev/null 2>&1 && echo "  ✅ Health check OK" || echo "  ❌ Health check failed"

echo ""
echo "🤖 Fondklik Bot:"
systemctl is-active fondklik-bot.service && echo "  ✅ Работает" || echo "  ❌ Остановлен"

echo ""
echo "💳 Payment Bot:"
systemctl is-active payment-bot.service && echo "  ✅ Работает" || echo "  ❌ Остановлен"

echo ""
echo "=========================================="
echo "✅ ДЕПЛОЙ ЗАВЕРШЕН!"
echo "=========================================="
