# 🔍 ПРОВЕРКА КОШЕЛЬКОВ НА VPS

## ❗ ПРОБЛЕМА:
Показывается тестовый кошелек `TPersistenceTest123456789012345678901234` вместо реального

---

## 📋 ПРОВЕРКА НА VPS:

```bash
# 1. Проверить активные кошельки в Payment Bot
cd /opt/fondklik/payment_bot
sqlite3 payment_bot.db "SELECT wallet_address, is_active, created_at FROM user_wallets WHERE is_active = 1 ORDER BY created_at DESC LIMIT 5;"

# 2. Проверить активные кошельки в Payment API
cd /opt/fondklik/payment_api
sqlite3 payments.db "SELECT wallet_address, is_active, created_at FROM user_wallets WHERE is_active = 1 ORDER BY created_at DESC LIMIT 5;" 2>/dev/null || echo "Таблица не найдена"

# 3. Проверить логи Payment API
journalctl -u payment-api.service -n 50 --no-pager | grep -E "(get-payment-wallet|wallet_address|ERROR)" | tail -15

# 4. Проверить, что Payment API видит базу данных
curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: $(curl -s http://localhost:8001/get-api-key | grep -o '"api_key":"[^"]*' | cut -d'"' -f4)" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test123"}' | jq .
```

---

**Пришлите результаты всех 4 команд!**

