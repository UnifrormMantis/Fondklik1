# 🚀 Установка с GitHub на VPS

## ШАГ 1: Клонирование репозитория на VPS

На VPS выполните:

```bash
# Установка git (если еще не установлен)
apt update -y
apt install -y git python3 python3-pip python3-venv curl sqlite3

# Переходим в рабочую директорию
cd /opt/fondklik

# Клонируем ваш репозиторий
# ЗАМЕНИТЕ URL_ВАШЕГО_РЕПОЗИТОРИЯ на реальный URL
git clone URL_ВАШЕГО_РЕПОЗИТОРИЯ ./bot

# Если у вас два разных репозитория для Payment API и бота:
# git clone URL_PAYMENT_API ./payment_api
# git clone URL_BOT ./bot
```

---

## ШАГ 2: Настройка структуры

```bash
cd /opt/fondklik

# Если в репозитории всё вместе, разделим:
# Если payment_api и bot в одном репо в разных папках:
# Нужно будет настроить структуру вручную

# Проверяем что есть
ls -la bot/
```

---

## ВАРИАНТ А: Если всё в одном репозитории

```bash
cd /opt/fondklik/bot

# Проверяем структуру
ls -la

# Если есть папка payment_api - копируем
if [ -d "payment_api" ]; then
    cp -r payment_api /opt/fondklik/
fi

# Если есть папка платежка - копируем
if [ -d "платежка" ]; then
    cp -r платежка /opt/fondklik/payment_api
fi
```

---

## ВАРИАНТ Б: Если два отдельных репозитория

```bash
cd /opt/fondklik

# Клонируем Payment API репозиторий
git clone URL_ПЛАТЕЖНОГО_РЕПО ./payment_api

# Клонируем бота репозиторий
git clone URL_БОТА_РЕПО ./bot
```

---

## ШАГ 3: Установка зависимостей

```bash
cd /opt/fondklik

# Payment API
cd payment_api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Бот
cd ../bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

cd /opt/fondklik
```

---

## ШАГ 4: Настройка переменных окружения

```bash
# Введите токен бота
read -p "Введите TELEGRAM_BOT_TOKEN: " BOT_TOKEN

# Создание .env для бота
cat > /opt/fondklik/bot/.env <<EOF
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
PAYMENT_API_URL=http://127.0.0.1:8001
EOF
```

---

## ШАГ 5: Создание systemd сервисов

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

# Перезагрузка systemd
systemctl daemon-reload
```

---

## ШАГ 6: Запуск

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


