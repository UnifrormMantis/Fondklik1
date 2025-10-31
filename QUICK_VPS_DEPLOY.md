# 🚀 БЫСТРАЯ УСТАНОВКА НА VPS

## ⚡ В 3 ШАГА

### 1️⃣ КОПИРОВАНИЕ ФАЙЛОВ НА VPS

**На вашем компьютере:**

```bash
VPS_USER="root"
VPS_IP="199.217.99.119"  # замените на ваш IP

# Копируем Payment API
scp -r /Users/roma/Desktop/платежка/* ${VPS_USER}@${VPS_IP}:/opt/fondklik/payment_api/

# Копируем главный бот
scp -r /Users/roma/Desktop/Fondklik/* ${VPS_USER}@${VPS_IP}:/opt/fondklik/bot/
```

---

### 2️⃣ ПОДКЛЮЧЕНИЕ К VPS

```bash
ssh root@199.217.99.119  # замените на ваш IP
```

---

### 3️⃣ ЗАПУСК УСТАНОВКИ

**На VPS выполните:**

```bash
# Переходим в директорию с ботом
cd /opt/fondklik/bot

# Запускаем установку
bash install_on_vps.sh
```

**Скрипт спросит токен бота - введите его.**

---

## ✅ ПРОВЕРКА

```bash
# Статус сервисов
sudo systemctl status payment-api.service
sudo systemctl status fondklik-bot.service

# Проверка API
curl http://localhost:8001/health
```

---

## 🐛 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

**Пришлите результат:**

```bash
sudo systemctl status payment-api.service --no-pager -l | head -20
sudo systemctl status fondklik-bot.service --no-pager -l | head -20
```

---

## 📋 СТРУКТУРА НА VPS

```
/opt/fondklik/
├── payment_api/          ← Payment API (порт 8001)
│   ├── simple_payment_api.py
│   └── venv/
└── bot/                  ← Главный бот
    ├── bot_fondklik_correct.py
    └── venv/
```

**Готово!** 🎉


