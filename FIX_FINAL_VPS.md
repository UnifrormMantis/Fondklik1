# ✅ ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ НА VPS

## ❗ ПРОБЛЕМЫ:
1. Метод `register_user_wallet` не существует в PaymentClient
2. В функции `create_deposit_payment` используется `user_wallet_from_db` вместо `user_wallet`

---

## 📋 ИСПРАВЛЕНИЕ НА VPS:

```bash
cd /opt/fondklik/bot

# 1. Исправить переменную в строке 860 и 2601 (обе должны быть user_wallet)
sed -i '860s/get_payment_wallet(user_wallet_from_db)/get_payment_wallet(user_wallet)/' bot_fondklik_correct.py
sed -i '2601s/get_payment_wallet(user_wallet_from_db)/get_payment_wallet(user_wallet)/' bot_fondklik_correct.py

# 2. Но подождите! Проверим где какая переменная определена
grep -B5 "get_payment_wallet(" bot_fondklik_correct.py | head -20

# Если в строке 860 должна быть user_wallet_from_db (проверим контекст):
# Откроем функцию чтобы понять:
sed -n '845,870p' bot_fondklik_correct.py

# 3. Удалить вызовы register_user_wallet (они не нужны)
# Найти все вызовы
grep -n "register_user_wallet" bot_fondklik_correct.py

# Удалить блоки с register_user_wallet
# Сначала посмотрим что там:
grep -A10 "register_user_wallet" bot_fondklik_correct.py | head -25

# Удалить блоки (вручную через sed сложно, лучше через Python или вручную)
# Временно закомментируем:
sed -i '/register_user_wallet/,+10s/^/# /' bot_fondklik_correct.py

# Или проще - заменить на комментарий:
sed -i 's/register_result = payment_client\.register_user_wallet/# register_result = payment_client.register_user_wallet/' bot_fondklik_correct.py

# 4. Перезапустить
systemctl restart fondklik-bot.service
sleep 3

# 5. Проверить
systemctl status fondklik-bot.service --no-pager -l | head -10
```

---

**Лучше просто заменить вызовы register_user_wallet на комментарии!**

