#!/bin/bash
# Скрипт установки с GitHub на VPS
# Выполняйте на VPS после подключения через SSH

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORK_DIR="/opt/fondklik"
REPO_URL="https://github.com/UnifrormMantis/FondKlik1.git"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  УСТАНОВКА С GITHUB${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 1. Установка системных зависимостей
echo -e "${YELLOW}[1/8] Установка системных зависимостей...${NC}"
apt update -y
apt install -y python3 python3-pip python3-venv curl git sqlite3
echo -e "${GREEN}✅ Готово${NC}"
echo ""

# 2. Создание директорий
echo -e "${YELLOW}[2/8] Создание директорий...${NC}"
mkdir -p "${WORK_DIR}"
mkdir -p "${WORK_DIR}/logs"
cd "${WORK_DIR}"
echo -e "${GREEN}✅ Готово${NC}"
echo ""

# 3. Клонирование репозитория
echo -e "${YELLOW}[3/8] Клонирование репозитория...${NC}"
if [ -d "bot" ]; then
    echo -e "${YELLOW}⚠️  Директория bot уже существует, обновляю...${NC}"
    cd bot
    git pull || true
    cd ..
else
    git clone "${REPO_URL}" bot
fi
echo -e "${GREEN}✅ Репозиторий склонирован${NC}"
echo ""

# 4. Организация структуры
echo -e "${YELLOW}[4/8] Организация структуры...${NC}"

# Проверяем где находится simple_payment_api.py
if [ -f "bot/simple_payment_api.py" ]; then
    # Если в корне репо - копируем в payment_api
    mkdir -p payment_api
    cp -r bot/simple_payment_api.py payment_api/ 2>/dev/null || true
    # Копируем нужные файлы для Payment API
    if [ -f "bot/database.py" ]; then
        cp bot/database.py payment_api/ 2>/dev/null || true
    fi
    if [ -f "bot/config.py" ]; then
        cp bot/config.py payment_api/ 2>/dev/null || true
    fi
    if [ -f "bot/tron_tracker.py" ]; then
        cp bot/tron_tracker.py payment_api/ 2>/dev/null || true
    fi
    if [ -f "bot/payment_integration.py" ]; then
        cp bot/payment_integration.py payment_api/ 2>/dev/null || true
    fi
    # Копируем requirements.txt если есть
    if [ -f "bot/requirements.txt" ]; then
        cp bot/requirements.txt payment_api/ 2>/dev/null || true
    fi
elif [ -d "bot/платежка" ]; then
    # Если есть папка платежка в репо
    cp -r bot/платежка/* payment_api/ 2>/dev/null || true
elif [ -d "bot/payment_api" ]; then
    # Если есть папка payment_api
    cp -r bot/payment_api/* payment_api/ 2>/dev/null || true
else
    echo -e "${YELLOW}⚠️  simple_payment_api.py не найден в репозитории${NC}"
    echo "Создаю симлинк..."
    ln -s bot payment_api 2>/dev/null || true
fi

echo -e "${GREEN}✅ Структура организована${NC}"
echo ""

# 5. Создание виртуальных окружений
echo -e "${YELLOW}[5/8] Создание виртуальных окружений...${NC}"

# Payment API
cd "${WORK_DIR}/payment_api"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
else
    pip install fastapi uvicorn pydantic requests python-dotenv tronpy aiohttp -q
fi
deactivate

# Бот
cd "${WORK_DIR}/bot"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
else
    pip install python-telegram-bot requests python-dotenv aiohttp APScheduler fastapi uvicorn pydantic -q
fi
deactivate

cd "${WORK_DIR}"
echo -e "${GREEN}✅ Виртуальные окружения созданы${NC}"
echo ""

# 6. Настройка переменных окружения
echo -e "${YELLOW}[6/8] Настройка переменных окружения...${NC}"
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    read -p "Введите TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${RED}❌ Токен бота обязателен!${NC}"
    exit 1
fi

cat > "${WORK_DIR}/bot/.env" <<EOF
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
PAYMENT_API_URL=http://127.0.0.1:8001
EOF

echo -e "${GREEN}✅ Переменные окружения настроены${NC}"
echo ""

# 7. Создание systemd сервисов
echo -e "${YELLOW}[7/8] Создание systemd сервисов...${NC}"

# Payment API сервис
cat > /etc/systemd/system/payment-api.service <<EOF
[Unit]
Description=Payment API Service (Fondklik)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${WORK_DIR}/payment_api
Environment="PATH=${WORK_DIR}/payment_api/venv/bin"
Environment="PORT=8001"
ExecStart=${WORK_DIR}/payment_api/venv/bin/python ${WORK_DIR}/payment_api/simple_payment_api.py
Restart=always
RestartSec=5
StandardOutput=append:${WORK_DIR}/logs/payment-api.log
StandardError=append:${WORK_DIR}/logs/payment-api-error.log

[Install]
WantedBy=multi-user.target
EOF

# Бот сервис
cat > /etc/systemd/system/fondklik-bot.service <<EOF
[Unit]
Description=Fondklik Telegram Bot
After=network.target payment-api.service
Requires=payment-api.service

[Service]
Type=simple
User=root
WorkingDirectory=${WORK_DIR}/bot
Environment="PATH=${WORK_DIR}/bot/venv/bin"
Environment="TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}"
Environment="PAYMENT_API_URL=http://127.0.0.1:8001"
ExecStart=${WORK_DIR}/bot/venv/bin/python ${WORK_DIR}/bot/bot_fondklik_correct.py
Restart=always
RestartSec=5
StandardOutput=append:${WORK_DIR}/logs/bot.log
StandardError=append:${WORK_DIR}/logs/bot-error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo -e "${GREEN}✅ Сервисы созданы${NC}"
echo ""

# 8. Запуск сервисов
echo -e "${YELLOW}[8/8] Запуск сервисов...${NC}"

# Остановка старых если есть
systemctl stop payment-api.service 2>/dev/null || true
systemctl stop fondklik-bot.service 2>/dev/null || true

# Запуск Payment API
systemctl enable payment-api.service
systemctl start payment-api.service
sleep 5

if systemctl is-active --quiet payment-api.service; then
    echo -e "${GREEN}✅ Payment API запущен${NC}"
else
    echo -e "${RED}❌ Ошибка запуска Payment API${NC}"
    echo "Логи: journalctl -u payment-api.service -n 50"
    exit 1
fi

# Запуск бота
systemctl enable fondklik-bot.service
systemctl start fondklik-bot.service
sleep 3

if systemctl is-active --quiet fondklik-bot.service; then
    echo -e "${GREEN}✅ Бот запущен${NC}"
else
    echo -e "${RED}❌ Ошибка запуска бота${NC}"
    echo "Логи: journalctl -u fondklik-bot.service -n 50"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  УСТАНОВКА ЗАВЕРШЕНА!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📊 Команды управления:"
echo "  systemctl status payment-api.service"
echo "  systemctl status fondklik-bot.service"
echo ""
echo "📝 Логи:"
echo "  journalctl -u payment-api.service -f"
echo "  journalctl -u fondklik-bot.service -f"
echo ""
echo "🔍 Проверка:"
echo "  curl http://localhost:8001/health"
echo ""
echo -e "${GREEN}✅ Готово к работе!${NC}"


