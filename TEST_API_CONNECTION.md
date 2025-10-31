# 🔍 Тест подключения к Payment API

## ✅ Проверка настроек:

Все настроено правильно:
- ✅ Админ добавлен: `8489431460`
- ✅ PAYMENT_API_KEY: `QGCHTq8vAjaeeSAXdzkH2OQMmyzfirvVKOxxxivNzyc`
- ✅ PAYMENT_API_URL: `http://127.0.0.1:8001`
- ✅ Environment переменные в systemd настроены

---

## 🧪 Тестирование:

Выполните на VPS:

```bash
# 1. Проверить что Payment API работает
curl http://localhost:8001/health

# 2. Тест получения кошелька через API
curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: QGCHTq8vAjaeeSAXdzkH2OQMmyzfirvVKOxxxivNzyc" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test"}' | python3 -m json.tool

# 3. Проверить логи бота - ищет ли он API
journalctl -u fondklik-bot.service -n 50 --no-pager | grep -i "payment\|api\|кошелек\|found\|используется"

# 4. Проверить что бот видит переменные окружения
journalctl -u fondklik-bot.service -n 50 --no-pager | grep -i "environment\|env\|api_url\|api_key"

# 5. Проверить активные кошельки в Payment Bot
curl -X GET http://localhost:8001/active-wallet \
  -H "X-API-Key: QGCHTq8vAjaeeSAXdzkH2OQMmyzfirvVKOxxxivNzyc" | python3 -m json.tool
```

---

## 🎯 Проверка в Telegram боте:

1. **Админ панель:**
   - Отправьте `/admin`
   - Должна открыться админ панель

2. **Синхронизация кошельков:**
   - Нажмите "Внести депозит" → "Оплатить"
   - Проверьте какой кошелек показывается
   - Должен быть кошелек из Payment Bot, а НЕ тестовый

---

**Выполните команды и проверьте бота!**

