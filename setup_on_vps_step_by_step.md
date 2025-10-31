# 📋 ПОШАГОВАЯ УСТАНОВКА НА VPS (выполняйте по порядку)

## ✅ Вы уже подключены к VPS! 

Теперь выполните команды **по порядку** на сервере:

---

## ШАГ 1: Подготовка системы

```bash
# Обновление системы
apt update -y

# Установка необходимых пакетов
apt install -y python3 python3-pip python3-venv curl git sqlite3

# Создание рабочих директорий
mkdir -p /opt/fondklik/payment_api
mkdir -p /opt/fondklik/bot
mkdir -p /opt/fondklik/logs

cd /opt/fondklik
```

---

## ШАГ 2: Копирование файлов (В НОВОМ ОКНЕ ТЕРМИНАЛА НА ВАШЕМ КОМПЬЮТЕРЕ)

**Откройте НОВОЕ окно терминала на вашем Mac** (не закрывайте SSH подключение!) и выполните:

```bash
# С вашего компьютера копируем файлы на VPS
cd /Users/roma/Desktop

# Копирование Payment API
scp -r платежка/* root@199.217.98.13:/opt/fondklik/payment_api/

# Копирование главного бота
scp -r Fondklik/* root@199.217.98.13:/opt/fondklik/bot/
```

**После копирования вернитесь к окну SSH с VPS и продолжите:**

---

## ШАГ 3: Проверка файлов (на VPS)

```bash
# Проверяем что файлы скопированы
ls -la /opt/fondklik/payment_api/simple_payment_api.py
ls -la /opt/fondklik/bot/bot_fondklik_correct.py

# Если файлы есть - продолжаем
```

---

## ШАГ 4: Установка зависимостей

```bash
cd /opt/fondklik

# Payment API - виртуальное окружение
cd payment_api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Бот - виртуальное окружение
cd ../bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

cd /opt/fondklik
```

---

## ШАГ 5: Настройка переменных окружения

```bash
# Введите токен бота (замените на ваш реальный токен)
read -p "Введите TELEGRAM_BOT_TOKEN: " BOT_TOKEN

# Создание .env файла для бота
cat > /opt/fondklik/bot/.env <<EOF
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
PAYMENT_API_URL=http://127.0.0.1:8001
EOF
```

---

## ШАГ 6: Создание systemd сервисов

```bash
# Сервис Payment API
cat > /etc/systemd/system/payment-api.service <<EOF
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

# Сервис бота
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

## ШАГ 7: Запуск сервисов

```bash
# Запуск Payment API
systemctl enable payment-api.service
systemctl start payment-api.service

# Ждем запуска (5 секунд)
sleep 5

# Проверка Payment API
systemctl status payment-api.service

# Запуск бота
systemctl enable fondklik-bot.service
systemctl start fondklik-bot.service

# Ждем запуска (3 секунды)
sleep 3

# Проверка бота
systemctl status fondklik-bot.service
```

---

## ШАГ 8: Проверка работы

```bash
# Проверка здоровья API
curl http://localhost:8001/health

# Проверка логов
tail -20 /opt/fondklik/logs/payment-api.log
tail -20 /opt/fondklik/logs/bot.log
```

---

## ✅ ГОТОВО!

Если оба сервиса запущены - боты работают! 🎉

### Полезные команды:

```bash
# Статус
systemctl status payment-api.service
systemctl status fondklik-bot.service

# Перезапуск
systemctl restart payment-api.service
systemctl restart fondklik-bot.service

# Логи
journalctl -u payment-api.service -f
journalctl -u fondklik-bot.service -f
```


