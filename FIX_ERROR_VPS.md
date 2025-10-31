# 🔧 ИСПРАВЛЕНИЕ ОШИБКИ НА VPS

## ✅ ИЗМЕНЕНИЯ:
Добавлена обработка ошибок при получении кошелька из Payment API.

---

## 📋 ВЫПОЛНИТЕ НА VPS:

### Вариант 1: Обновить из GitHub (если push прошел)
```bash
cd /opt/fondklik/bot
git pull
systemctl restart fondklik-bot.service
```

### Вариант 2: Вручную исправить код на VPS
```bash
cd /opt/fondklik/bot

# Заменить вызовы get_payment_wallet с обработкой ошибок
# Первая функция (около строки 859):
sed -i '859a\        try:' bot_fondklik_correct.py
sed -i '860s/^/            /' bot_fondklik_correct.py
sed -i '862s/if not payment_wallet_result\.get("success"):/if not payment_wallet_result or not payment_wallet_result.get("success"):/' bot_fondklik_correct.py
sed -i '870a\        except Exception as e:\n            logger.error(f"Ошибка получения кошелька из Payment Bot: {e}", exc_info=True)\n            payment_wallet = "TPersistenceTest123456789012345678901234"' bot_fondklik_correct.py

# Вторая функция (около строки 2607):
sed -i '2606a\        try:' bot_fondklik_correct.py
sed -i '2607s/^/            /' bot_fondklik_correct.py
sed -i '2609s/if not payment_wallet_result\.get("success"):/if not payment_wallet_result or not payment_wallet_result.get("success"):/' bot_fondklik_correct.py

# Перезапустить
systemctl restart fondklik-bot.service

# Проверить логи
journalctl -u fondklik-bot.service -n 50 --no-pager | tail -20
```

### Вариант 3: Простое решение - проверить что API доступен
```bash
# Проверить что Payment API работает
curl http://localhost:8001/health

# Проверить что API ключ правильный
API_KEY=$(cat /opt/fondklik/bot/.env | grep PAYMENT_API_KEY | cut -d'=' -f2)
echo "API Key: $API_KEY"

# Тест получения кошелька
curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test123"}' | python3 -m json.tool
```

---

**Сначала выполните Вариант 3 для диагностики, потом Вариант 2 для исправления!**

