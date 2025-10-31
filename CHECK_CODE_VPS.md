# ✅ ПРОВЕРКА КОДА БОТА НА VPS

## 📋 ВЫПОЛНИТЕ:

```bash
# 1. Проверить что код использует get_payment_wallet (не get_active_wallet)
grep -n "get_payment_wallet\|get_active_wallet" /opt/fondklik/bot/bot_fondklik_correct.py | head -10

# 2. Проверить что есть обработка ошибок (try-except)
grep -B2 -A5 "get_payment_wallet(user_wallet" /opt/fondklik/bot/bot_fondklik_correct.py | head -15

# 3. Если видите get_active_wallet - нужно заменить вручную
# Сначала проверьте:
grep -n "get_active_wallet()" /opt/fondklik/bot/bot_fondklik_correct.py
```

---

**Если в выводе команды 1 есть `get_active_wallet` - код не обновился!**

Выполните замену:
```bash
cd /opt/fondklik/bot

# Заменить get_active_wallet на get_payment_wallet (с параметром)
# Первое место (около строки 860):
sed -i 's/payment_client\.get_active_wallet()/payment_client.get_payment_wallet(user_wallet_from_db)/g' bot_fondklik_correct.py

# Второе место (около строки 2601):
sed -i 's/payment_client\.get_active_wallet()/payment_client.get_payment_wallet(user_wallet)/g' bot_fondklik_correct.py

# Проверить что заменилось
grep -n "get_payment_wallet" bot_fondklik_correct.py | head -3

# Перезапустить
systemctl restart fondklik-bot.service
sleep 3

# Проверить статус
systemctl status fondklik-bot.service --no-pager -l | head -10
```

---

**Выполните команды проверки и пришлите результаты!**

