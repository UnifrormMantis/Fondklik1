# 🚀 УСТАНОВКА С GITHUB НА VPS

## Репозиторий: https://github.com/UnifrormMantis/FondKlik1

---

## ⚡ БЫСТРЫЙ СТАРТ

### На VPS выполните:

```bash
# 1. Установка git и зависимостей
apt update -y
apt install -y git python3 python3-pip python3-venv curl sqlite3

# 2. Скачивание скрипта установки
cd /opt/fondklik
curl -o install_from_github.sh https://raw.githubusercontent.com/UnifrormMantis/FondKlik1/main/install_from_github.sh

# Или копируйте скрипт вручную, или выполните всё по шагам:
```

---

## 📋 РУЧНАЯ УСТАНОВКА (пошагово)

### ШАГ 1: Подготовка

```bash
apt update -y
apt install -y git python3 python3-pip python3-venv curl sqlite3
mkdir -p /opt/fondklik/logs
cd /opt/fondklik
```

### ШАГ 2: Клонирование репозитория

```bash
git clone https://github.com/UnifrormMantis/FondKlik1.git bot
```

### ШАГ 3: Организация структуры

```bash
cd /opt/fondklik

# Создаем директорию для Payment API
mkdir -p payment_api

# Копируем нужные файлы для Payment API
cp bot/simple_payment_api.py payment_api/ 2>/dev/null || true
cp bot/database.py payment_api/ 2>/dev/null || true
cp bot/config.py payment_api/ 2>/dev/null || true
cp bot/tron_tracker.py payment_api/ 2>/dev/null || true
cp bot/payment_integration.py payment_api/ 2>/dev/null || true
cp bot/requirements.txt payment_api/ 2>/dev/null || true
```

### ШАГ 4: Установка зависимостей

```bash
# Payment API
cd /opt/fondklik/payment_api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || pip install fastapi uvicorn pydantic requests python-dotenv tronpy aiohttp
deactivate

# Бот
cd /opt/fondklik/bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || pip install python-telegram-bot requests python-dotenv aiohttp APScheduler fastapi uvicorn pydantic
deactivate
```

### ШАГ 5: Настройка переменных окружения

```bash
read -p "Введите TELEGRAM_BOT_TOKEN: " BOT_TOKEN

cat > /opt/fondklik/bot/.env <<EOF
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
PAYMENT_API_URL=http://127.0.0.1:8001
EOF
```

### ШАГ 6: Создание systemd сервисов

```bash
# Payment API сервис
cat > /etc/systemd/system/payment-api.service <<'EOF'
[Unit]
Description=Payment API Service (Fondklik)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fondklik/payment_api
Environment="PATH=/opt/fondklik/payment_api/venv/bin"
Environment="PORT=8001"
ExecStart=/opt/fondklik/payment_api/venv/bin/python /opt/fondklik/payment_api/simple_payment_api.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/fondklik/logs/payment-api.log
StandardError=append:/opt/fondklik/logs/payment-api-error.log

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
WorkingDirectory=/opt/fondklik/bot
Environment="PATH=/opt/fondklik/bot/venv/bin"
Environment="TELEGRAM_BOT_TOKEN=${BOT_TOKEN}"
Environment="PAYMENT_API_URL=http://127.0.0.1:8001"
ExecStart=/opt/fondklik/bot/venv/bin/python /opt/fondklik/bot/bot_fondklik_correct.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/fondklik/logs/bot.log
StandardError=append:/opt/fondklik/logs/bot-error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
```

### ШАГ 7: Запуск

```bash
# Запуск Payment API
systemctl enable payment-api.service
systemctl start payment-api.service
sleep 5

# Запуск бота
systemctl enable fondklik-bot.service
systemctl start fondklik-bot.service
sleep 3

# Проверка
systemctl status payment-api.service
systemctl status fondklik-bot.service
curl http://localhost:8001/health
```

---

## ✅ ПРОВЕРКА

```bash
# Статус сервисов
systemctl status payment-api.service
systemctl status fondklik-bot.service

# Логи
journalctl -u payment-api.service -f
journalctl -u fondklik-bot.service -f

# Health check
curl http://localhost:8001/health
```

---

## 🔄 ОБНОВЛЕНИЕ

```bash
cd /opt/fondklik/bot
git pull
systemctl restart payment-api.service
systemctl restart fondklik-bot.service
```

---

## 📞 ПОМОЩЬ

Если что-то не работает:
```bash
# Проверьте логи
journalctl -u payment-api.service -n 50
journalctl -u fondklik-bot.service -n 50
```


