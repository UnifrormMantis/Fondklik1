# 🔍 Проверка и исправление интеграции

## ✅ ЧТО НУЖНО ПРОВЕРИТЬ И ИСПРАВИТЬ:

1. **Админ права в Fondklik** - добавить ID `8489431460`
2. **Синхронизация между ботами** - проверить API ключ и URL
3. **Работоспособность Payment API** - проверить доступность

---

## 📋 ВЫПОЛНИТЕ НА VPS:

```bash
# 1. Добавить админа в Fondklik бота
cd /opt/fondklik/bot
sqlite3 bot_database.db "INSERT OR IGNORE INTO admins (telegram_id) VALUES (8489431460);"

# 2. Проверить что админ добавлен
sqlite3 bot_database.db "SELECT * FROM admins;"

# 3. Получить API ключ из Payment API
curl http://localhost:8001/get-api-key | grep -o '"api_key":"[^"]*' | cut -d'"' -f4

# 4. Проверить что Payment API работает
curl http://localhost:8001/health

# 5. Проверить переменные окружения бота
cat /opt/fondklik/bot/.env
# Должно быть:
# TELEGRAM_BOT_TOKEN=...
# PAYMENT_API_URL=http://127.0.0.1:8001
# PAYMENT_API_KEY=... (из шага 3)

# 6. Проверить что Payment Client использует правильный ключ
grep -n "PAYMENT_API_KEY" /opt/fondklik/bot/payment_client.py | head -3

# 7. Если API ключ в payment_client.py не совпадает - нужно установить переменную окружения:
# В файле /opt/fondklik/bot/.env добавить:
# PAYMENT_API_KEY=<ключ_из_шага_3>

# 8. Перезапустить сервисы
systemctl restart fondklik-bot.service payment-api.service
sleep 3

# 9. Проверить статусы
systemctl status fondklik-bot.service --no-pager -l | head -15
systemctl status payment-api.service --no-pager -l | head -15
```

---

## 🔧 ЕСЛИ API КЛЮЧ НЕ СОВПАДАЕТ:

```bash
# 1. Получить актуальный API ключ
API_KEY=$(curl -s http://localhost:8001/get-api-key | grep -o '"api_key":"[^"]*' | cut -d'"' -f4)
echo "API Key: $API_KEY"

# 2. Добавить в .env бота
cd /opt/fondklik/bot
echo "PAYMENT_API_KEY=$API_KEY" >> .env

# 3. Обновить systemd сервис
sudo sed -i "s|Environment=\"PAYMENT_API_URL=|Environment=\"PAYMENT_API_KEY=${API_KEY}\"\nEnvironment=\"PAYMENT_API_URL=|g" /etc/systemd/system/fondklik-bot.service

# 4. Перезагрузить systemd и перезапустить
systemctl daemon-reload
systemctl restart fondklik-bot.service
```

---

## ✅ ПРОВЕРКА РАБОТЫ:

1. В Telegram боте Fondklik должна работать команда `/admin`
2. В разделе "Внести депозит" → "Оплатить" должен подтягиваться кошелек из Payment API
3. Кнопка "Проверить платеж" должна проверять через Payment API

---

**Выполните команды на VPS и пришлите результаты!**

