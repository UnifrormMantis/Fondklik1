# 🔧 ИСПРАВЛЕНИЕ ОБЕИХ ФУНКЦИЙ НА VPS

## ❗ ПРОБЛЕМА:
В строке 860 должна быть переменная `user_wallet_from_db`, а в строке 2601 - `user_wallet`.

---

## 📋 ИСПРАВЛЕНИЕ НА VPS:

```bash
cd /opt/fondklik/bot

# Проверить текущее состояние
grep -n "get_payment_wallet(" bot_fondklik_correct.py | head -3

# Исправить строку 860 (должна быть user_wallet_from_db)
sed -i '860s/get_payment_wallet(user_wallet)/get_payment_wallet(user_wallet_from_db)/' bot_fondklik_correct.py

# Исправить строку 2601 (должна быть user_wallet)
sed -i '2601s/get_payment_wallet(user_wallet_from_db)/get_payment_wallet(user_wallet)/' bot_fondklik_correct.py

# Проверить что исправлено
grep -n "get_payment_wallet(" bot_fondklik_correct.py | head -3
# Должно показать:
# 860: ... get_payment_wallet(user_wallet_from_db)
# 2601: ... get_payment_wallet(user_wallet)

# Перезапустить бота
systemctl restart fondklik-bot.service
sleep 3

# Проверить статус
systemctl status fondklik-bot.service --no-pager -l | head -10
```

---

**Выполните команды и проверьте работу бота в Telegram!**

