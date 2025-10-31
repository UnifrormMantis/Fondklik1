#!/bin/bash
# =============================================================================
# СКРИПТ УСТАНОВКИ БОТОВ НА VPS (BitLauncher)
# =============================================================================
# Этот скрипт устанавливает:
# 1. Payment API (simple_payment_api.py) на порту 8001
# 2. Главный бот (bot_fondklik_correct.py)
# =============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================

# Директории проекта
VPS_WORK_DIR="/opt/fondklik"
PAYMENT_API_DIR="${VPS_WORK_DIR}/payment_api"
BOT_DIR="${VPS_WORK_DIR}/bot"

# Порты
PAYMENT_API_PORT=8001

# Python версия
PYTHON_VERSION="python3"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  УСТАНОВКА БОТОВ НА VPS${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# =============================================================================
# ШАГ 1: ПРОВЕРКА И УСТАНОВКА ЗАВИСИМОСТЕЙ СИСТЕМЫ
# =============================================================================

echo -e "${YELLOW}[1/8] Проверка системных зависимостей...${NC}"

# Обновление пакетов
sudo apt update -y

# Установка необходимых пакетов
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    ufw \
    sqlite3

echo -e "${GREEN}✅ Системные зависимости установлены${NC}"
echo ""

# =============================================================================
# ШАГ 2: СОЗДАНИЕ РАБОЧИХ ДИРЕКТОРИЙ
# =============================================================================

echo -e "${YELLOW}[2/8] Создание рабочих директорий...${NC}"

sudo mkdir -p "${VPS_WORK_DIR}"
sudo mkdir -p "${PAYMENT_API_DIR}"
sudo mkdir -p "${BOT_DIR}"
sudo mkdir -p "${VPS_WORK_DIR}/logs"

# Установка прав
sudo chown -R $USER:$USER "${VPS_WORK_DIR}"

echo -e "${GREEN}✅ Директории созданы${NC}"
echo ""

# =============================================================================
# ШАГ 3: ПОЛУЧЕНИЕ ИНФОРМАЦИИ О ПРОЕКТАХ
# =============================================================================

echo -e "${YELLOW}[3/8] Настройка проекта...${NC}"
echo ""
echo -e "Вам нужно будет указать:"
echo -e "  1. TELEGRAM_BOT_TOKEN - токен главного бота"
echo -e "  2. PAYMENT_API_KEY - API ключ (будет сгенерирован автоматически после запуска)"
echo ""

# Запрашиваем токен бота
read -p "Введите TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${RED}❌ Токен бота обязателен!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Токен получен${NC}"
echo ""

# =============================================================================
# ШАГ 4: СОЗДАНИЕ ВИРТУАЛЬНЫХ ОКРУЖЕНИЙ
# =============================================================================

echo -e "${YELLOW}[4/8] Создание виртуальных окружений...${NC}"

# Виртуальное окружение для Payment API
if [ ! -d "${PAYMENT_API_DIR}/venv" ]; then
    ${PYTHON_VERSION} -m venv "${PAYMENT_API_DIR}/venv"
    echo -e "${GREEN}✅ Виртуальное окружение для Payment API создано${NC}"
else
    echo -e "${YELLOW}⚠️  Виртуальное окружение для Payment API уже существует${NC}"
fi

# Виртуальное окружение для бота
if [ ! -d "${BOT_DIR}/venv" ]; then
    ${PYTHON_VERSION} -m venv "${BOT_DIR}/venv"
    echo -e "${GREEN}✅ Виртуальное окружение для бота создано${NC}"
else
    echo -e "${YELLOW}⚠️  Виртуальное окружение для бота уже существует${NC}"
fi

echo ""

# =============================================================================
# ШАГ 5: УСТАНОВКА ЗАВИСИМОСТЕЙ
# =============================================================================

echo -e "${YELLOW}[5/8] Установка зависимостей...${NC}"

# Активируем и обновляем pip для Payment API
source "${PAYMENT_API_DIR}/venv/bin/activate"
pip install --upgrade pip

# Проверяем наличие requirements.txt для Payment API
if [ -f "/Users/roma/Desktop/платежка/requirements.txt" ]; then
    echo "Установка зависимостей для Payment API..."
    pip install -r /Users/roma/Desktop/платежка/requirements.txt
    echo -e "${GREEN}✅ Зависимости Payment API установлены${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt для Payment API не найден, устанавливаю базовые...${NC}"
    pip install fastapi uvicorn pydantic requests python-dotenv tronpy aiohttp
fi

deactivate

# Активируем и обновляем pip для бота
source "${BOT_DIR}/venv/bin/activate"
pip install --upgrade pip

# Проверяем наличие requirements.txt для бота
if [ -f "/Users/roma/Desktop/Fondklik/requirements.txt" ]; then
    echo "Установка зависимостей для бота..."
    pip install -r /Users/roma/Desktop/Fondklik/requirements.txt
    echo -e "${GREEN}✅ Зависимости бота установлены${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt для бота не найден, устанавливаю базовые...${NC}"
    pip install python-telegram-bot requests python-dotenv aiohttp APScheduler fastapi uvicorn pydantic
fi

deactivate

echo ""

# =============================================================================
# ШАГ 6: КОПИРОВАНИЕ ФАЙЛОВ ПРОЕКТА
# =============================================================================

echo -e "${YELLOW}[6/8] Копирование файлов проекта...${NC}"
echo ""
echo -e "${YELLOW}⚠️  ВАЖНО: Вам нужно скопировать файлы на VPS вручную!${NC}"
echo ""
echo "Выполните следующие команды на вашем локальном компьютере:"
echo ""
echo -e "${GREEN}# Копирование Payment API:${NC}"
echo "scp -r /Users/roma/Desktop/платежка/* user@your_vps_ip:${PAYMENT_API_DIR}/"
echo ""
echo -e "${GREEN}# Копирование главного бота:${NC}"
echo "scp -r /Users/roma/Desktop/Fondklik/* user@your_vps_ip:${BOT_DIR}/"
echo ""
read -p "Нажмите Enter после копирования файлов на VPS..."
echo ""

# =============================================================================
# ШАГ 7: СОЗДАНИЕ SYSTEMD СЕРВИСОВ
# =============================================================================

echo -e "${YELLOW}[7/8] Создание systemd сервисов...${NC}"

# Сервис для Payment API
sudo tee /etc/systemd/system/payment-api.service > /dev/null <<EOF
[Unit]
Description=Payment API Service (Fondklik)
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=${PAYMENT_API_DIR}
Environment="PATH=${PAYMENT_API_DIR}/venv/bin"
Environment="PORT=${PAYMENT_API_PORT}"
ExecStart=${PAYMENT_API_DIR}/venv/bin/python ${PAYMENT_API_DIR}/simple_payment_api.py
Restart=always
RestartSec=5
StandardOutput=append:${VPS_WORK_DIR}/logs/payment-api.log
StandardError=append:${VPS_WORK_DIR}/logs/payment-api-error.log

[Install]
WantedBy=multi-user.target
EOF

# Сервис для главного бота
sudo tee /etc/systemd/system/fondklik-bot.service > /dev/null <<EOF
[Unit]
Description=Fondklik Telegram Bot
After=network.target payment-api.service
Requires=payment-api.service

[Service]
Type=simple
User=$USER
WorkingDirectory=${BOT_DIR}
Environment="PATH=${BOT_DIR}/venv/bin"
Environment="TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}"
Environment="PAYMENT_API_URL=http://127.0.0.1:${PAYMENT_API_PORT}"
ExecStart=${BOT_DIR}/venv/bin/python ${BOT_DIR}/bot_fondklik_correct.py
Restart=always
RestartSec=5
StandardOutput=append:${VPS_WORK_DIR}/logs/bot.log
StandardError=append:${VPS_WORK_DIR}/logs/bot-error.log

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
sudo systemctl daemon-reload

echo -e "${GREEN}✅ Systemd сервисы созданы${NC}"
echo ""

# =============================================================================
# ШАГ 8: НАСТРОЙКА ФАЙРВОЛА И ЗАПУСК СЕРВИСОВ
# =============================================================================

echo -e "${YELLOW}[8/8] Настройка файрвола и запуск сервисов...${NC}"

# Открываем порт для Payment API (если нужно извне)
# sudo ufw allow ${PAYMENT_API_PORT}/tcp

# Включаем Payment API
sudo systemctl enable payment-api.service
sudo systemctl start payment-api.service

# Ждем запуска API
echo "Ожидание запуска Payment API (5 секунд)..."
sleep 5

# Проверяем статус Payment API
if sudo systemctl is-active --quiet payment-api.service; then
    echo -e "${GREEN}✅ Payment API запущен${NC}"
else
    echo -e "${RED}❌ Ошибка запуска Payment API${NC}"
    echo "Проверьте логи: sudo journalctl -u payment-api.service -n 50"
    exit 1
fi

# Получаем API ключ
echo "Получение API ключа..."
sleep 2
API_KEY_RESPONSE=$(curl -s http://localhost:${PAYMENT_API_PORT}/get-api-key || echo "")
if [ ! -z "$API_KEY_RESPONSE" ]; then
    PAYMENT_API_KEY=$(echo "$API_KEY_RESPONSE" | grep -o '"api_key":"[^"]*' | cut -d'"' -f4)
    if [ ! -z "$PAYMENT_API_KEY" ]; then
        echo -e "${GREEN}✅ API ключ получен: ${PAYMENT_API_KEY}${NC}"
        
        # Обновляем сервис бота с API ключом
        sudo sed -i "s|Environment=\"PAYMENT_API_URL=|Environment=\"PAYMENT_API_KEY=${PAYMENT_API_KEY}\"\\nEnvironment=\"PAYMENT_API_URL=|g" /etc/systemd/system/fondklik-bot.service
        sudo systemctl daemon-reload
    fi
fi

# Включаем и запускаем бот
sudo systemctl enable fondklik-bot.service
sudo systemctl start fondklik-bot.service

# Ждем запуска бота
echo "Ожидание запуска бота (3 секунды)..."
sleep 3

# Проверяем статус бота
if sudo systemctl is-active --quiet fondklik-bot.service; then
    echo -e "${GREEN}✅ Бот запущен${NC}"
else
    echo -e "${RED}❌ Ошибка запуска бота${NC}"
    echo "Проверьте логи: sudo journalctl -u fondklik-bot.service -n 50"
    exit 1
fi

echo ""

# =============================================================================
# ФИНАЛЬНАЯ ИНФОРМАЦИЯ
# =============================================================================

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  УСТАНОВКА ЗАВЕРШЕНА!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📊 СТАТУС СЕРВИСОВ:"
echo "  Payment API:  sudo systemctl status payment-api.service"
echo "  Бот:          sudo systemctl status fondklik-bot.service"
echo ""
echo "📝 КОМАНДЫ УПРАВЛЕНИЯ:"
echo "  Запуск:       sudo systemctl start payment-api fondklik-bot"
echo "  Остановка:    sudo systemctl stop payment-api fondklik-bot"
echo "  Перезапуск:   sudo systemctl restart payment-api fondklik-bot"
echo "  Логи:         sudo journalctl -u payment-api.service -f"
echo "                sudo journalctl -u fondklik-bot.service -f"
echo ""
echo "🔍 ПРОВЕРКА:"
echo "  Health API:   curl http://localhost:${PAYMENT_API_PORT}/health"
echo "  API Key:      curl http://localhost:${PAYMENT_API_PORT}/get-api-key"
echo ""
echo "📁 ДИРЕКТОРИИ:"
echo "  Payment API:  ${PAYMENT_API_DIR}"
echo "  Бот:          ${BOT_DIR}"
echo "  Логи:         ${VPS_WORK_DIR}/logs"
echo ""
echo -e "${GREEN}✅ Всё готово!${NC}"
echo ""


