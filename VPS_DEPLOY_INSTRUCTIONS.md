# 🚀 ИНСТРУКЦИЯ ПО ДЕПЛОЮ НА VPS (BitLauncher)

## 📋 ЧТО НУЖНО ПЕРЕД НАЧАЛОМ

1. **Доступ к VPS по SSH**
2. **Токен Telegram бота** (`TELEGRAM_BOT_TOKEN`)
3. **Все файлы проекта** скопированы на VPS

---

## 🎯 БЫСТРЫЙ СТАРТ (ВЫПОЛНЯЙТЕ НА VPS)

### ШАГ 1: Подготовка системы

```bash
# Обновление системы
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv curl git ufw sqlite3

# Создание рабочей директории
sudo mkdir -p /opt/fondklik/{payment_api,bot,logs}
sudo chown -R $USER:$USER /opt/fondklik
cd /opt/fondklik
```

---

### ШАГ 2: Копирование файлов с локального компьютера

**На вашем локальном компьютере выполните:**

```bash
# Замените user@your_vps_ip на ваши данные SSH
VPS_USER="root"  # или ваш пользователь
VPS_IP="199.217.99.119"  # ваш IP VPS

# Копирование Payment API из папки "платежка"
scp -r /Users/roma/Desktop/платежка/* ${VPS_USER}@${VPS_IP}:/opt/fondklik/payment_api/

# Копирование главного бота из папки "Fondklik"
scp -r /Users/roma/Desktop/Fondklik/* ${VPS_USER}@${VPS_IP}:/opt/fondklik/bot/
```

**Или используйте rsync (быстрее):**

```bash
rsync -avz --progress /Users/roma/Desktop/платежка/ ${VPS_USER}@${VPS_IP}:/opt/fondklik/payment_api/
rsync -avz --progress /Users/roma/Desktop/Fondklik/ ${VPS_USER}@${VPS_IP}:/opt/fondklik/bot/
```

---

### ШАГ 3: Установка на VPS (продолжение на VPS)

```bash
cd /opt/fondklik

# 1. Создание виртуальных окружений
python3 -m venv payment_api/venv
python3 -m venv bot/venv

# 2. Установка зависимостей Payment API
source payment_api/venv/bin/activate
pip install --upgrade pip
pip install -r payment_api/requirements.txt
deactivate

# 3. Установка зависимостей бота
source bot/venv/bin/activate
pip install --upgrade pip
pip install -r bot/requirements.txt
deactivate

# 4. Установка переменных окружения
# Укажите ваш TELEGRAM_BOT_TOKEN
read -p "Введите TELEGRAM_BOT_TOKEN: " BOT_TOKEN

# Сохраняем в файл для бота
cat > bot/.env <<EOF
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
PAYMENT_API_URL=http://127.0.0.1:8001
EOF
```

---

### ШАГ 4: Создание systemd сервисов

```bash
# Сервис для Payment API
sudo tee /etc/systemd/system/payment-api.service > /dev/null <<'EOF'
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

# Сервис для главного бота
sudo tee /etc/systemd/system/fondklik-bot.service > /dev/null <<EOF
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
sudo systemctl daemon-reload
```

---

### ШАГ 5: Запуск сервисов

```bash
# Запуск Payment API
sudo systemctl enable payment-api.service
sudo systemctl start payment-api.service

# Ждем запуска API (5 секунд)
sleep 5

# Проверка статуса Payment API
sudo systemctl status payment-api.service

# Получение API ключа (если нужно)
curl http://localhost:8001/get-api-key

# Запуск бота
sudo systemctl enable fondklik-bot.service
sudo systemctl start fondklik-bot.service

# Проверка статуса бота
sudo systemctl status fondklik-bot.service
```

---

## ✅ ПРОВЕРКА РАБОТЫ

```bash
# Проверка здоровья Payment API
curl http://localhost:8001/health

# Проверка статусов сервисов
sudo systemctl status payment-api.service --no-pager -l | head -20
sudo systemctl status fondklik-bot.service --no-pager -l | head -20

# Просмотр логов
sudo journalctl -u payment-api.service -n 50 --no-pager
sudo journalctl -u fondklik-bot.service -n 50 --no-pager
```

---

## 🔧 УПРАВЛЕНИЕ СЕРВИСАМИ

```bash
# Запуск
sudo systemctl start payment-api fondklik-bot

# Остановка
sudo systemctl stop payment-api fondklik-bot

# Перезапуск
sudo systemctl restart payment-api fondklik-bot

# Статус
sudo systemctl status payment-api.service
sudo systemctl status fondklik-bot.service

# Логи в реальном времени
sudo journalctl -u payment-api.service -f
sudo journalctl -u fondklik-bot.service -f

# Логи из файлов
tail -f /opt/fondklik/logs/payment-api.log
tail -f /opt/fondklik/logs/bot.log
```

---

## 🐛 РЕШЕНИЕ ПРОБЛЕМ

### Если Payment API не запускается:

```bash
# Проверка логов
sudo journalctl -u payment-api.service -n 50 --no-pager

# Проверка вручную
cd /opt/fondklik/payment_api
source venv/bin/activate
python simple_payment_api.py
```

### Если бот не запускается:

```bash
# Проверка логов
sudo journalctl -u fondklik-bot.service -n 50 --no-pager

# Проверка токена
echo $TELEGRAM_BOT_TOKEN

# Проверка вручную
cd /opt/fondklik/bot
source venv/bin/activate
python bot_fondklik_correct.py
```

### Если порт 8001 занят:

```bash
# Проверка занятости порта
sudo netstat -tulpn | grep 8001

# Остановка процесса на порту
sudo kill $(sudo lsof -t -i:8001)
```

---

## 📊 СТРУКТУРА ПРОЕКТА НА VPS

```
/opt/fondklik/
├── payment_api/          # Payment API проект
│   ├── venv/            # Виртуальное окружение
│   ├── simple_payment_api.py
│   ├── requirements.txt
│   └── ...
├── bot/                  # Главный бот
│   ├── venv/            # Виртуальное окружение
│   ├── bot_fondklik_correct.py
│   ├── requirements.txt
│   ├── .env            # Переменные окружения
│   └── ...
└── logs/                 # Логи
    ├── payment-api.log
    ├── payment-api-error.log
    ├── bot.log
    └── bot-error.log
```

---

## 🔐 БЕЗОПАСНОСТЬ

```bash
# Открытие порта 8001 только для внутренних запросов (рекомендуется)
# Если нужен доступ извне:
sudo ufw allow 8001/tcp

# Но лучше оставить только локально (127.0.0.1)
```

---

## 📞 ТЕСТИРОВАНИЕ

После запуска в Telegram боте:

1. Нажмите **"Внести депозит"** → **"Оплатить"**
   - Должен подтягиваться актуальный кошелёк из Payment API

2. Нажмите **"Проверить платеж"**
   - Должны увидеть: "Платеж ещё не поступил" или "Платеж подтвержден"

---

## ✅ ГОТОВО!

Если всё работает - система полностью настроена и готова к использованию! 🎉


