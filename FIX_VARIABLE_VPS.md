# 🔧 ИСПРАВЛЕНИЕ ПЕРЕМЕННОЙ НА VPS

## ❗ ПРОБЛЕМА:
В строке 2601 используется неправильная переменная `user_wallet_from_db` вместо `user_wallet`.

---

## 📋 ИСПРАВЛЕНИЕ НА VPS:

```bash
cd /opt/fondklik/bot

# Исправить переменную на строке 2601
sed -i '2601s/user_wallet_from_db/user_wallet/' bot_fondklik_correct.py

# Проверить что исправлено
grep -n "get_payment_wallet(user_wallet)" bot_fondklik_correct.py | head -3

# Перезапустить бота
systemctl restart fondklik-bot.service
sleep 3

# Проверить статус
systemctl status fondklik-bot.service --no-pager -l | head -10
```

---

**Выполните команды и проверьте работу бота!**

