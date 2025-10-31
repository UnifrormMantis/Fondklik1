# 🚀 УСТАНОВКА НА VPS 199.217.98.13

## ⚡ БЫСТРЫЙ СТАРТ

### ШАГ 1: Копирование файлов (на вашем компьютере)

```bash
cd /Users/roma/Desktop/Fondklik
bash copy_to_vps.sh
```

**Или вручную:**

```bash
VPS_IP="199.217.98.13"

# Создание директорий
ssh root@${VPS_IP} "mkdir -p /opt/fondklik/payment_api /opt/fondklik/bot /opt/fondklik/logs"

# Копирование Payment API
scp -r /Users/roma/Desktop/платежка/* root@${VPS_IP}:/opt/fondklik/payment_api/

# Копирование главного бота
scp -r /Users/roma/Desktop/Fondklik/* root@${VPS_IP}:/opt/fondklik/bot/
```

---

### ШАГ 2: Подключение и установка (на VPS)

```bash
# Подключение к VPS
ssh root@199.217.98.13

# На VPS выполните:
cd /opt/fondklik/bot
bash install_on_vps.sh
```

**Когда скрипт спросит токен - введите ваш `TELEGRAM_BOT_TOKEN`**

---

### ШАГ 3: Проверка

```bash
# Проверка статуса
sudo systemctl status payment-api.service
sudo systemctl status fondklik-bot.service

# Проверка здоровья API
curl http://localhost:8001/health

# Просмотр логов
sudo journalctl -u payment-api.service -f
sudo journalctl -u fondklik-bot.service -f
```

---

## 🐛 ЕСЛИ ПРОБЛЕМЫ

Пришлите результат:

```bash
sudo systemctl status payment-api.service --no-pager -l | head -20
sudo systemctl status fondklik-bot.service --no-pager -l | head -20
```

---

## 📞 ПОЛЕЗНЫЕ КОМАНДЫ

```bash
# Перезапуск сервисов
sudo systemctl restart payment-api.service
sudo systemctl restart fondklik-bot.service

# Остановка
sudo systemctl stop payment-api.service
sudo systemctl stop fondklik-bot.service

# Запуск
sudo systemctl start payment-api.service
sudo systemctl start fondklik-bot.service

# Логи в реальном времени
sudo journalctl -u payment-api.service -f
sudo journalctl -u fondklik-bot.service -f
```


