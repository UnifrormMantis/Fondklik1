# 🔍 ОТЛАДКА БОТА НА VPS

## 📋 ПРОВЕРКА:

```bash
# 1. Проверить логи бота (файл логов, не journalctl)
tail -50 /opt/fondklik/logs/bot.log

# 2. Проверить логи ошибок
tail -50 /opt/fondklik/logs/bot-error.log

# 3. Проверить что API работает
curl http://localhost:8001/health

# 4. Проверить получение кошелька через API
API_KEY=$(cat /opt/fondklik/bot/.env | grep PAYMENT_API_KEY | cut -d'=' -f2)
echo "API Key: $API_KEY"

curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test123"}' | python3 -m json.tool

# 5. Проверить что код обновился (должен быть get_payment_wallet)
grep -n "get_payment_wallet\|get_active_wallet" /opt/fondklik/bot/bot_fondklik_correct.py | head -5

# 6. Проверить переменные окружения в systemd
grep -A3 "PAYMENT" /etc/systemd/system/fondklik-bot.service

# 7. Проверить последние логи в реальном времени (после нажатия кнопки в боте)
journalctl -u fondklik-bot.service -f --no-pager
```

---

**Выполните команды 1-6 и пришлите результаты!**

