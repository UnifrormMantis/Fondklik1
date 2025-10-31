# ✅ Проверка интеграции после настройки

## 📋 Выполните на VPS для финальной проверки:

```bash
# 1. Проверить статусы сервисов
systemctl status payment-api.service --no-pager -l | head -20
systemctl status fondklik-bot.service --no-pager -l | head -20

# 2. Проверить что API ключ правильный в системе
cat /opt/fondklik/bot/.env | grep PAYMENT

# 3. Проверить что админ в базе
sqlite3 /opt/fondklik/bot/bot_database.db "SELECT * FROM admins;"

# 4. Тест API - получить кошелек
curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: QGCHTq8vAjaeeSAXdzkH2OQMmyzfirvVKOxxxivNzyc" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test"}'

# 5. Проверить логи бота на предмет подключения к API
journalctl -u fondklik-bot.service -n 30 --no-pager | grep -i "payment\|api\|кошелек"

# 6. Проверить логи API
journalctl -u payment-api.service -n 20 --no-pager
```

---

## 🧪 Проверка в Telegram боте:

1. **Админ панель:**
   - Отправьте `/admin` в боте Fondklik
   - Должна открыться админ панель

2. **Проверка синхронизации:**
   - Нажмите "Внести депозит" → "Оплатить"
   - Должен показаться кошелек из Payment Bot (активный кошелек)
   - НЕ тестовый кошелек!

3. **Проверка платежа:**
   - Нажмите "Проверить платеж"
   - Должна быть проверка через Payment API

---

## 🔍 Если что-то не работает:

### API ключ не совпадает:
```bash
# Получить актуальный ключ
API_KEY=$(curl -s http://localhost:8001/get-api-key | grep -o '"api_key":"[^"]*' | cut -d'"' -f4)

# Обновить .env
cd /opt/fondklik/bot
sed -i "s|PAYMENT_API_KEY=.*|PAYMENT_API_KEY=$API_KEY|g" .env

# Обновить systemd
sudo sed -i "s|Environment=\"PAYMENT_API_KEY=.*|Environment=\"PAYMENT_API_KEY=$API_KEY\"|g" /etc/systemd/system/fondklik-bot.service

# Перезапустить
sudo systemctl daemon-reload
sudo systemctl restart fondklik-bot.service
```

### Бот не видит API:
```bash
# Проверить что API работает
curl http://localhost:8001/health

# Проверить логи бота
journalctl -u fondklik-bot.service -f
```

---

**Выполните команды проверки и пришлите результаты!**

