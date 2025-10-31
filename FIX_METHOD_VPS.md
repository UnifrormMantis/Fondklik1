# ✅ ИСПРАВЛЕНИЕ МЕТОДА НА VPS

## ❗ ПРОБЛЕМА:
Код использует `get_active_wallet()` вместо `get_payment_wallet(user_wallet)`
API работает и возвращает правильный кошелек!

---

## 📋 ИСПРАВЛЕНИЕ НА VPS:

```bash
cd /opt/fondklik/bot

# 1. Заменить get_active_wallet на get_payment_wallet с правильными параметрами
# Строка 860 - использовать user_wallet_from_db (определена выше в функции)
sed -i '860s/payment_client\.get_active_wallet()/payment_client.get_payment_wallet(user_wallet_from_db)/' bot_fondklik_correct.py

# Строка 2601 - использовать user_wallet (определена в этой функции)
sed -i '2601s/payment_client\.get_active_wallet()/payment_client.get_payment_wallet(user_wallet)/' bot_fondklik_correct.py

# 2. Проверить что заменилось
grep -n "get_payment_wallet\|get_active_wallet" bot_fondklik_correct.py | head -5
# Должно показать только get_payment_wallet

# 3. Проверить синтаксис
python3 -m py_compile bot_fondklik_correct.py

# 4. Перезапустить бота
systemctl restart fondklik-bot.service
sleep 3

# 5. Проверить статус
systemctl status fondklik-bot.service --no-pager -l | head -10

# 6. Проверить логи после нажатия "Оплатить"
journalctl -u fondklik-bot.service -n 30 --no-pager | grep -i "кошелек\|wallet\|payment" | tail -10
```

---

**Выполните все команды по порядку!**

