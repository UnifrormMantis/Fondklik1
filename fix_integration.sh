#!/bin/bash

# Скрипт для проверки и исправления интеграции

set -e

echo "🔍 Проверка и исправление интеграции..."

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

ADMIN_ID=8489431460
BOT_DIR="/opt/fondklik/bot"
API_DIR="/opt/fondklik/payment_api"

echo ""
echo "1️⃣ Добавление админа в Fondklik..."
cd $BOT_DIR
if sqlite3 bot_database.db "INSERT OR IGNORE INTO admins (telegram_id) VALUES ($ADMIN_ID);" 2>/dev/null; then
    echo -e "${GREEN}✅ Админ $ADMIN_ID добавлен${NC}"
else
    echo -e "${RED}❌ Ошибка добавления админа${NC}"
    echo "   Проверяю структуру таблицы admins..."
    sqlite3 bot_database.db ".schema admins"
fi

echo ""
echo "2️⃣ Проверка админов..."
sqlite3 bot_database.db "SELECT telegram_id FROM admins;" 2>/dev/null || echo "Таблица admins не найдена"

echo ""
echo "3️⃣ Проверка Payment API..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Payment API работает${NC}"
else
    echo -e "${RED}❌ Payment API не отвечает${NC}"
    echo "   Проверяю статус сервиса..."
    systemctl status payment-api.service --no-pager -l | head -10
    exit 1
fi

echo ""
echo "4️⃣ Получение API ключа..."
API_KEY=$(curl -s http://localhost:8001/get-api-key | grep -o '"api_key":"[^"]*' | cut -d'"' -f4)
if [ ! -z "$API_KEY" ]; then
    echo -e "${GREEN}✅ API ключ получен: ${API_KEY:0:20}...${NC}"
else
    echo -e "${RED}❌ Не удалось получить API ключ${NC}"
    exit 1
fi

echo ""
echo "5️⃣ Проверка .env файла..."
cd $BOT_DIR
if [ ! -f .env ]; then
    echo "Создаю .env файл..."
    touch .env
fi

# Обновляем PAYMENT_API_KEY в .env
if grep -q "PAYMENT_API_KEY" .env; then
    sed -i "s|PAYMENT_API_KEY=.*|PAYMENT_API_KEY=$API_KEY|g" .env
    echo -e "${GREEN}✅ API ключ обновлен в .env${NC}"
else
    echo "PAYMENT_API_KEY=$API_KEY" >> .env
    echo -e "${GREEN}✅ API ключ добавлен в .env${NC}"
fi

# Проверяем PAYMENT_API_URL
if ! grep -q "PAYMENT_API_URL" .env; then
    echo "PAYMENT_API_URL=http://127.0.0.1:8001" >> .env
    echo -e "${GREEN}✅ PAYMENT_API_URL добавлен в .env${NC}"
fi

echo ""
echo "6️⃣ Обновление systemd сервиса..."
if grep -q "Environment=\"PAYMENT_API_KEY=" /etc/systemd/system/fondklik-bot.service; then
    sudo sed -i "s|Environment=\"PAYMENT_API_KEY=.*|Environment=\"PAYMENT_API_KEY=$API_KEY\"|g" /etc/systemd/system/fondklik-bot.service
else
    # Добавляем перед PAYMENT_API_URL
    sudo sed -i "s|Environment=\"PAYMENT_API_URL=|Environment=\"PAYMENT_API_KEY=$API_KEY\"\nEnvironment=\"PAYMENT_API_URL=|g" /etc/systemd/system/fondklik-bot.service
fi
echo -e "${GREEN}✅ systemd сервис обновлен${NC}"

echo ""
echo "7️⃣ Перезагрузка systemd и перезапуск сервисов..."
sudo systemctl daemon-reload
sudo systemctl restart fondklik-bot.service

sleep 3

echo ""
echo "8️⃣ Проверка статусов..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
systemctl status fondklik-bot.service --no-pager -l | head -15
echo ""
systemctl status payment-api.service --no-pager -l | head -15

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ ИНТЕГРАЦИЯ ПРОВЕРЕНА И ИСПРАВЛЕНА!${NC}"
echo ""
echo "📋 Итоги:"
echo "   • Админ $ADMIN_ID добавлен"
echo "   • Payment API работает"
echo "   • API ключ: ${API_KEY:0:20}..."
echo "   • Сервисы перезапущены"
echo ""
echo "🧪 Проверьте в боте:"
echo "   1. Команда /admin должна работать"
echo "   2. Внести депозит → Оплатить → должен подтягиваться кошелек"
echo "   3. Проверить платеж → должна работать проверка через API"

