# 🤖 Установка Payment Bot на VPS (второй бот)

## 📋 ТЕКУЩАЯ СТРУКТУРА НА VPS:

```
/opt/fondklik/
├── payment_api/          # Payment API (порт 8001) ✅
│   └── simple_payment_api.py
└── bot/                  # Fondklik Bot ✅
    └── bot_fondklik_correct.py
```

## ➕ ДОБАВИМ:

```
/opt/fondklik/
└── payment_bot/          # Payment Bot (второй бот) 🆕
    └── main.py
```

---

## 🚀 ИНСТРУКЦИЯ ПО УСТАНОВКЕ

### ШАГ 1: На VPS выполните

```bash
# Подключитесь к VPS
ssh root@199.217.98.13

# Создаем директорию для Payment Bot
mkdir -p /opt/fondklik/payment_bot
cd /opt/fondklik

# Клонируем репозиторий Payment Bot
git clone https://github.com/UnifrormMantis/PaymentBot.git payment_bot
```

---

### ШАГ 2: Установка зависимостей

```bash
cd /opt/fondklik/payment_bot

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt

deactivate
cd /opt/fondklik
```

---

### ШАГ 3: Настройка переменных окружения

```bash
# Введите токен для Payment Bot (ОТЛИЧНЫЙ от Fondklik бота!)
read -p "Введите TELEGRAM_BOT_TOKEN для Payment Bot: " PAYMENT_BOT_TOKEN

# Создаем .env файл
cat > /opt/fondklik/payment_bot/.env <<EOF
TELEGRAM_BOT_TOKEN=${PAYMENT_BOT_TOKEN}
TRON_API_KEY=
CHECK_INTERVAL=30
EOF
```

**⚠️ ВАЖНО:** Это должен быть **ДРУГОЙ токен**, не тот что у Fondklik бота!

---

### ШАГ 4: Создание systemd сервиса

```bash
# Сервис для Payment Bot
cat > /etc/systemd/system/payment-bot.service <<EOF
[Unit]
Description=Payment Bot (Second Bot)
After=network.target payment-api.service
Requires=payment-api.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fondklik/payment_bot
Environment="PATH=/opt/fondklik/payment_bot/venv/bin"
Environment="TELEGRAM_BOT_TOKEN=\${PAYMENT_BOT_TOKEN}"
ExecStart=/opt/fondklik/payment_bot/venv/bin/python /opt/fondklik/payment_bot/main.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/fondklik/logs/payment-bot.log
StandardError=append:/opt/fondklik/logs/payment-bot-error.log

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
systemctl daemon-reload
```

**⚠️ ВАЖНО:** Замените `${PAYMENT_BOT_TOKEN}` на реальный токен или используйте переменную окружения!

---

### ШАГ 5: Обновление сервиса с токеном

```bash
# Введите токен еще раз
read -p "Введите TELEGRAM_BOT_TOKEN для Payment Bot: " PAYMENT_BOT_TOKEN

# Обновляем сервис с токеном
sed -i "s|Environment=\"TELEGRAM_BOT_TOKEN=\\\${PAYMENT_BOT_TOKEN}\"|Environment=\"TELEGRAM_BOT_TOKEN=${PAYMENT_BOT_TOKEN}\"|g" /etc/systemd/system/payment-bot.service

# Перезагружаем systemd
systemctl daemon-reload
```

---

### ШАГ 6: Запуск Payment Bot

```bash
# Запускаем Payment Bot
systemctl enable payment-bot.service
systemctl start payment-bot.service

# Ждем 3 секунды
sleep 3

# Проверяем статус
systemctl status payment-bot.service --no-pager -l | head -20
```

---

### ШАГ 7: Проверка всех сервисов

```bash
# Проверка всех трех сервисов
echo "=== Payment API ==="
systemctl is-active payment-api.service

echo "=== Fondklik Bot ==="
systemctl is-active fondklik-bot.service

echo "=== Payment Bot ==="
systemctl is-active payment-bot.service

# Проверка здоровья API
curl -s http://localhost:8001/health
```

---

## 📊 ФИНАЛЬНАЯ СТРУКТУРА:

```
/opt/fondklik/
├── payment_api/          # Payment API (порт 8001)
│   ├── simple_payment_api.py
│   └── venv/
├── bot/                  # Fondklik Bot (первый бот)
│   ├── bot_fondklik_correct.py
│   └── venv/
├── payment_bot/          # Payment Bot (второй бот) 🆕
│   ├── main.py
│   ├── private_bot.py
│   └── venv/
└── logs/                 # Логи всех сервисов
    ├── payment-api.log
    ├── bot.log
    └── payment-bot.log
```

---

## ✅ ПРОВЕРКА РАБОТЫ:

### Все сервисы должны быть активны:

```bash
systemctl status payment-api.service --no-pager -l | head -5
systemctl status fondklik-bot.service --no-pager -l | head -5
systemctl status payment-bot.service --no-pager -l | head -5
```

### В Telegram:

1. **Fondklik Bot** - должен отвечать (первый бот)
2. **Payment Bot** - должен отвечать (второй бот, другой токен!)

---

## 🔧 УПРАВЛЕНИЕ:

```bash
# Запуск
systemctl start payment-api.service
systemctl start fondklik-bot.service
systemctl start payment-bot.service

# Остановка
systemctl stop payment-api.service
systemctl stop fondklik-bot.service
systemctl stop payment-bot.service

# Перезапуск
systemctl restart payment-api.service
systemctl restart fondklik-bot.service
systemctl restart payment-bot.service

# Логи
journalctl -u payment-api.service -f
journalctl -u fondklik-bot.service -f
journalctl -u payment-bot.service -f
```

---

## ⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ:

1. **Разные токены:** Fondklik Bot и Payment Bot должны иметь **разные** TELEGRAM_BOT_TOKEN
2. **Не конфликтуют:** Они работают как отдельные боты в Telegram
3. **Один API:** Оба бота могут использовать один Payment API на порту 8001
4. **Разные базы:** Каждый бот использует свою базу данных

---

## 🐛 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ:

```bash
# Проверьте логи
journalctl -u payment-bot.service -n 50 --no-pager

# Проверьте токен
cat /opt/fondklik/payment_bot/.env

# Проверьте процессы
ps aux | grep python
```

---

**Готово! Теперь на VPS работают три сервиса:** Payment API + Fondklik Bot + Payment Bot! 🎉

