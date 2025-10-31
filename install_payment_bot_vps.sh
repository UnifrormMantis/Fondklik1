#!/bin/bash
# Скрипт установки Payment Bot на VPS
# Выполняйте на VPS после подключения через SSH

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

WORK_DIR="/opt/fondklik"
PAYMENT_BOT_DIR="${WORK_DIR}/payment_bot"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  УСТАНОВКА PAYMENT BOT НА VPS${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Проверка что мы на VPS
if [ ! -d "/opt/fondklik/payment_api" ]; then
    echo -e "${RED}❌ Payment API не найден!${NC}"
    echo "Сначала установите Payment API и Fondklik Bot"
    exit 1
fi

echo -e "${YELLOW}[1/6] Создание директории и клонирование...${NC}"
mkdir -p "${PAYMENT_BOT_DIR}"
cd "${WORK_DIR}"

# Клонирование репозитория
if [ ! -d "payment_bot/.git" ]; then
    git clone https://github.com/UnifrormMantis/PaymentBot.git payment_bot
    echo -e "${GREEN}✅ Репозиторий склонирован${NC}"
else
    echo -e "${YELLOW}⚠️  Репозиторий уже существует, обновляю...${NC}"
    cd payment_bot
    git pull || true
    cd ..
fi
echo ""

echo -e "${YELLOW}[2/6] Установка зависимостей...${NC}"
cd "${PAYMENT_BOT_DIR}"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate

cd "${WORK_DIR}"
echo -e "${GREEN}✅ Зависимости установлены${NC}"
echo ""

echo -e "${YELLOW}[3/6] Настройка переменных окружения...${NC}"
read -p "Введите TELEGRAM_BOT_TOKEN для Payment Bot (ОТЛИЧНЫЙ от Fondklik бота!): " PAYMENT_BOT_TOKEN

if [ -z "$PAYMENT_BOT_TOKEN" ]; then
    echo -e "${RED}❌ Токен обязателен!${NC}"
    exit 1
fi

cat > "${PAYMENT_BOT_DIR}/.env" <<EOF
TELEGRAM_BOT_TOKEN=${PAYMENT_BOT_TOKEN}
TRON_API_KEY=
CHECK_INTERVAL=30
EOF

echo -e "${GREEN}✅ Переменные окружения настроены${NC}"
echo ""

echo -e "${YELLOW}[4/6] Создание systemd сервиса...${NC}"
cat > /etc/systemd/system/payment-bot.service <<EOF
[Unit]
Description=Payment Bot (Second Bot)
After=network.target payment-api.service
Requires=payment-api.service

[Service]
Type=simple
User=root
WorkingDirectory=${PAYMENT_BOT_DIR}
Environment="PATH=${PAYMENT_BOT_DIR}/venv/bin"
Environment="TELEGRAM_BOT_TOKEN=${PAYMENT_BOT_TOKEN}"
ExecStart=${PAYMENT_BOT_DIR}/venv/bin/python ${PAYMENT_BOT_DIR}/main.py
Restart=always
RestartSec=5
StandardOutput=append:${WORK_DIR}/logs/payment-bot.log
StandardError=append:${WORK_DIR}/logs/payment-bot-error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo -e "${GREEN}✅ Сервис создан${NC}"
echo ""

echo -e "${YELLOW}[5/6] Запуск Payment Bot...${NC}"
systemctl enable payment-bot.service
systemctl start payment-bot.service
sleep 3

if systemctl is-active --quiet payment-bot.service; then
    echo -e "${GREEN}✅ Payment Bot запущен${NC}"
else
    echo -e "${RED}❌ Ошибка запуска Payment Bot${NC}"
    echo "Логи: journalctl -u payment-bot.service -n 50"
    exit 1
fi
echo ""

echo -e "${YELLOW}[6/6] Проверка всех сервисов...${NC}"
echo "Payment API:  $(systemctl is-active payment-api.service)"
echo "Fondklik Bot: $(systemctl is-active fondklik-bot.service)"
echo "Payment Bot:  $(systemctl is-active payment-bot.service)"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  УСТАНОВКА ЗАВЕРШЕНА!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📊 Команды управления:"
echo "  systemctl status payment-bot.service"
echo "  journalctl -u payment-bot.service -f"
echo ""
echo "✅ Все три сервиса работают:"
echo "  1. Payment API (порт 8001)"
echo "  2. Fondklik Bot (первый бот)"
echo "  3. Payment Bot (второй бот)"
echo ""

