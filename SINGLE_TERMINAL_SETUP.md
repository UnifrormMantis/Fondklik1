# 🚀 Установка из одного окна терминала

## ВАРИАНТ: Всё последовательно

### ШАГ 1: На VPS (в окне SSH)

```bash
# 1. Установка пакетов (если еще не сделали)
apt update -y
apt install -y python3 python3-pip python3-venv curl git sqlite3

# 2. ВЫХОДИМ ИЗ SSH (чтобы скопировать файлы)
exit
```

---

### ШАГ 2: На вашем Mac (в том же окне терминала)

```bash
# Копирование файлов
cd /Users/roma/Desktop

# Payment API
scp -r платежка/* root@199.217.98.13:/opt/fondklik/payment_api/

# Главный бот
scp -r Fondklik/* root@199.217.98.13:/opt/fondklik/bot/
```

---

### ШАГ 3: Снова подключаемся к VPS

```bash
ssh root@199.217.98.13
cd /opt/fondklik

# Проверяем файлы
ls -la payment_api/simple_payment_api.py
ls -la bot/bot_fondklik_correct.py
```

---

### ШАГ 4: Продолжаем установку (на VPS)

```bash
# Создание виртуальных окружений

# Payment API
cd /opt/fondklik/payment_api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Бот
cd /opt/fondklik/bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

cd /opt/fondklik
```

---

### ШАГ 5: Настройка и запуск

```bash
# Введите токен бота
read -p "Введите TELEGRAM_BOT_TOKEN: " BOT_TOKEN

# Создание .env
cat > /opt/fondklik/bot/.env <<EOF
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
PAYMENT_API_URL=http://127.0.0.1:8001
EOF

# Создание systemd сервисов (скопируйте из следующего шага)
```

---

### ШАГ 6: Systemd сервисы

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

# Запуск
systemctl enable payment-api.service
systemctl start payment-api.service
sleep 5

systemctl enable fondklik-bot.service
systemctl start fondklik-bot.service
sleep 3

# Проверка
systemctl status payment-api.service
systemctl status fondklik-bot.service
curl http://localhost:8001/health
```


