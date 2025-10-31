# 🔍 ОТЛАДКА ПРОБЛЕМЫ С КОШЕЛЬКОМ

## ❗ ПРОБЛЕМА:
Все еще показывается тестовый кошелек `TPersistenceTest123456789012345678901234`

---

## 📋 ПРОВЕРКА НА VPS:

```bash
# 1. Проверить какой метод используется
grep -n "get_payment_wallet\|get_active_wallet" /opt/fondklik/bot/bot_fondklik_correct.py | head -5

# 2. Проверить логи когда нажимается "Оплатить"
# Сначала нажмите "Оплатить" в боте, потом:
journalctl -u fondklik-bot.service -n 50 --no-pager | grep -i "payment\|кошелек\|wallet\|error" | tail -20

# 3. Проверить что API работает и возвращает кошелек
API_KEY=$(cat /opt/fondklik/bot/.env | grep PAYMENT_API_KEY | cut -d'=' -f2)
curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test123"}' | python3 -m json.tool

# 4. Проверить что payment_client правильно работает
cd /opt/fondklik/bot
python3 <<EOF
import sys
sys.path.insert(0, '/opt/fondklik/bot')
from payment_client import payment_client
result = payment_client.get_payment_wallet("test123")
print("Result:", result)
EOF

# 5. Если используется get_active_wallet - нужно заменить
# Проверить:
grep -n "get_active_wallet()" /opt/fondklik/bot/bot_fondklik_correct.py

# Если найдено - заменить:
# sed -i 's/payment_client\.get_active_wallet()/payment_client.get_payment_wallet(user_wallet_from_db)/g' bot_fondklik_correct.py
```

---

**Выполните команды 1, 2, 3 и пришлите результаты!**

