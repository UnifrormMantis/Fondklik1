# ✅ Финальная проверка работы

## 📊 Проверка логов бота

Выполните на VPS:

```bash
# Проверить последние логи бота
journalctl -u fondklik-bot.service -n 50 --no-pager | tail -30

# Проверить есть ли ошибки
journalctl -u fondklik-bot.service -n 100 --no-pager | grep -i "error\|exception\|traceback"

# Проверить подключение к API
journalctl -u fondklik-bot.service -n 100 --no-pager | grep -i "payment\|api\|кошелек"
```

---

## 🧪 Проверка в Telegram боте Fondklik:

### 1. Админ панель:
- Отправьте команду `/admin` в боте
- Должна открыться админ панель с кнопками
- Если говорит "нет доступа" - админ не добавлен

### 2. Проверка синхронизации кошельков:
- Нажмите кнопку "Внести депозит"
- Нажмите "Оплатить"
- **Проверьте какой кошелек показывается:**
  - ✅ Если показывает кошелек из Payment Bot (тот что вы добавили) - синхронизация работает
  - ❌ Если показывает тестовый "TYourPaymentWallet..." - синхронизация НЕ работает

### 3. Проверка платежа:
- После получения кошелька нажмите "Проверить платеж"
- Должна быть проверка через Payment API

---

## 🔍 Если админ панель не работает:

```bash
# Проверить админа в базе
sqlite3 /opt/fondklik/bot/bot_database.db "SELECT telegram_id FROM admins;"

# Если нет вашего ID (8489431460) - добавить
sqlite3 /opt/fondklik/bot/bot_database.db "INSERT OR IGNORE INTO admins (telegram_id) VALUES (8489431460);"
systemctl restart fondklik-bot.service
```

---

## 🔍 Если синхронизация не работает:

```bash
# 1. Проверить что Payment API работает
curl http://localhost:8001/health

# 2. Проверить .env файл
cat /opt/fondklik/bot/.env

# 3. Проверить systemd конфигурацию
cat /etc/systemd/system/fondklik-bot.service | grep -A3 PAYMENT

# 4. Проверить что API ключ правильный
API_KEY=$(curl -s http://localhost:8001/get-api-key | grep -o '"api_key":"[^"]*' | cut -d'"' -f4)
echo "Текущий API ключ: $API_KEY"

# 5. Проверить в payment_client.py что используется правильный ключ
grep "PAYMENT_API_KEY" /opt/fondklik/bot/payment_client.py | head -3

# 6. Тест API вручную
curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test"}' | python3 -m json.tool
```

---

**Выполните команды и проверьте бота в Telegram! Пришлите результаты.**

