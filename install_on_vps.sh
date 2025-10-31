#!/bin/bash
# =============================================================================
# ПРОСТОЙ СКРИПТ УСТАНОВКИ НА VPS
# Скопируйте этот файл на VPS и запустите: bash install_on_vps.sh
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORK_DIR="/opt/fondklik"
PAYMENT_DIR="${WORK_DIR}/payment_api"
BOT_DIR="${WORK_DIR}/bot"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  УСТАНОВКА БОТОВ НА VPS${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Проверка: должны быть в рабочей директории
if [ ! -f "payment_api/simple_payment_api.py" ] || [ ! -f "bot/bot_fondklik_correct.py" ]; then
    echo -e "${RED}❌ ОШИБКА: Файлы проекта не найдены!${NC}"
    echo ""
    echo "Убедитесь что:"
    echo "  1. payment_api/simple_payment_api.py существует"
    echo "  2. bot/bot_fondklik_correct.py существует"
    echo ""
    echo "Текущая директория: $(pwd)"
    echo "Структура должна быть:"
    echo "  ./payment_api/  - файлы Payment API"
    echo "  ./bot/          - файлы главного бота"
    exit 1
fi

# Обновление системы
echo -e "${YELLOW}[1/6] Установка системных зависимостей...${NC}"
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv curl sqlite3 ufw 2>/dev/null || true
echo -e "${GREEN}✅ Готово${NC}"
echo ""

# Создание директорий
echo -e "${YELLOW}[2/6] Создание директорий...${NC}"
sudo mkdir -p "${WORK_DIR}/logs"
sudo chown -R $USER:$USER "${WORK_DIR}" 2>/dev/null || true
echo -e "${GREEN}✅ Готово${NC}"
echo ""

# Создание venv
echo -e "${YELLOW}[3/6] Создание виртуальных окружений...${NC}"
cd "${PAYMENT_DIR}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>/dev/null || pip install fastapi uvicorn pydantic requests python-dotenv tronpy aiohttp -q
deactivate

cd "${BOT_DIR}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>/dev/null || pip install python-telegram-bot requests python-dotenv aiohttp APScheduler fastapi uvicorn pydantic -q
deactivate

cd "${WORK_DIR}"
echo -e "${GREEN}✅ Готово${NC}"
echo ""

# Получение токена бота
echo -e "${YELLOW}[4/6] Настройка переменных окружения...${NC}"
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    read -p "Введите TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${RED}❌ Токен бота обязателен!${NC}"
    exit 1
fi

# Создание .env для бота
cat > "${BOT_DIR}/.env" <<EOF
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
PAYMENT_API_URL=http://127.0.0.1:8001
EOF

echo -e "${GREEN}✅ Готово${NC}"
echo ""

# Создание systemd сервисов
echo -e "${YELLOW}[5/6] Создание systemd сервисов...${NC}"

# Payment API сервис
sudo tee /etc/systemd/system/payment-api.service > /dev/null <<EOF
[Unit]
Description=Payment API Service (Fondklik)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${PAYMENT_DIR}
Environment="PATH=${PAYMENT_DIR}/venv/bin"
Environment="PORT=8001"
ExecStart=${PAYMENT_DIR}/venv/bin/python ${PAYMENT_DIR}/simple_payment_api.py
Restart=always
RestartSec=5
StandardOutput=append:${WORK_DIR}/logs/payment-api.log
StandardError=append:${WORK_DIR}/logs/payment-api-error.log

[Install]
WantedBy=multi-user.target
EOF

# Бот сервис
sudo tee /etc/systemd/system/fondklik-bot.service > /dev/null <<EOF
[Unit]
Description=Fondklik Telegram Bot
After=network.target payment-api.service
Requires=payment-api.service

[Service]
Type=simple
User=root
WorkingDirectory=${BOT_DIR}
Environment="PATH=${BOT_DIR}/venv/bin"
Environment="TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}"
Environment="PAYMENT_API_URL=http://127.0.0.1:8001"
ExecStart=${BOT_DIR}/venv/bin/python ${BOT_DIR}/bot_fondklik_correct.py
Restart=always
RestartSec=5
StandardOutput=append:${WORK_DIR}/logs/bot.log
StandardError=append:${WORK_DIR}/logs/bot-error.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo -e "${GREEN}✅ Готово${NC}"
echo ""

# Запуск сервисов
echo -e "${YELLOW}[6/6] Запуск сервисов...${NC}"

# Остановка старых сервисов если есть
sudo systemctl stop payment-api.service 2>/dev/null || true
sudo systemctl stop fondklik-bot.service 2>/dev/null || true

# Запуск Payment API
sudo systemctl enable payment-api.service
sudo systemctl start payment-api.service
sleep 5

# Проверка Payment API
if sudo systemctl is-active --quiet payment-api.service; then
    echo -e "${GREEN}✅ Payment API запущен${NC}"
else
    echo -e "${RED}❌ Ошибка запуска Payment API${NC}"
    echo "Логи: sudo journalctl -u payment-api.service -n 50"
    exit 1
fi

# Запуск бота
sudo systemctl enable fondklik-bot.service
sudo systemctl start fondklik-bot.service
sleep 3

# Проверка бота
if sudo systemctl is-active --quiet fondklik-bot.service; then
    echo -e "${GREEN}✅ Бот запущен${NC}"
else
    echo -e "${RED}❌ Ошибка запуска бота${NC}"
    echo "Логи: sudo journalctl -u fondklik-bot.service -n 50"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  УСТАНОВКА ЗАВЕРШЕНА!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📊 Команды управления:"
echo "  sudo systemctl status payment-api.service"
echo "  sudo systemctl status fondklik-bot.service"
echo ""
echo "📝 Логи:"
echo "  sudo journalctl -u payment-api.service -f"
echo "  sudo journalctl -u fondklik-bot.service -f"
echo ""
echo "🔍 Проверка:"
echo "  curl http://localhost:8001/health"
echo ""
echo -e "${GREEN}✅ Готово к работе!${NC}"


