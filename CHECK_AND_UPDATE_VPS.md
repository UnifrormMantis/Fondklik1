# 🔍 ПРОВЕРКА И ОБНОВЛЕНИЕ БОТА НА VPS

## ❗ ПРОБЛЕМА:
Бот все еще показывает тестовый кошелек - значит код не обновился на VPS.

---

## 📋 ВЫПОЛНИТЕ НА VPS:

```bash
# 1. Перейти в директорию бота
cd /opt/fondklik/bot

# 2. Проверить текущую версию (последний коммит)
git log -1 --oneline

# 3. Проверить что мы на правильной ветке
git branch

# 4. Получить последние изменения из GitHub
git fetch origin

# 5. Проверить что есть новые коммиты
git log HEAD..origin/main --oneline

# 6. Обновить код
git pull origin main

# 7. Проверить что изменения применены - найти get_payment_wallet
grep -n "get_payment_wallet" bot_fondklik_correct.py | head -3

# 8. Если не видно get_payment_wallet - значит код не обновился
# Проверить вручную:
grep -n "get_active_wallet\|get_payment_wallet" bot_fondklik_correct.py | head -5

# 9. Перезапустить бота
systemctl restart fondklik-bot.service
sleep 3

# 10. Проверить статус
systemctl status fondklik-bot.service --no-pager -l | head -15

# 11. Проверить логи - должны быть вызовы get_payment_wallet
journalctl -u fondklik-bot.service -n 50 --no-pager | grep -i "payment\|кошелек" | tail -10
```

---

## 🔍 ЕСЛИ КОД НЕ ОБНОВЛЯЕТСЯ:

### Вариант 1: Принудительное обновление

```bash
cd /opt/fondklik/bot

# Сохранить локальные изменения (если есть)
git stash

# Принудительно обновить
git fetch origin
git reset --hard origin/main

# Проверить изменения
grep -n "get_payment_wallet" bot_fondklik_correct.py | head -3
```

### Вариант 2: Вручную изменить код

```bash
cd /opt/fondklik/bot

# Найти все вызовы get_active_wallet
grep -n "get_active_wallet" bot_fondklik_correct.py

# Заменить вручную (замените строки на основе вывода grep)
sed -i 's/payment_client\.get_active_wallet()/payment_client.get_payment_wallet(user_wallet_from_db)/g' bot_fondklik_correct.py
sed -i 's/payment_client\.get_active_wallet()/payment_client.get_payment_wallet(user_wallet)/g' bot_fondklik_correct.py

# Проверить изменения
grep -n "get_payment_wallet" bot_fondklik_correct.py | head -3

# Перезапустить
systemctl restart fondklik-bot.service
```

---

**Выполните команды проверки и пришлите результаты шагов 2, 6, 7, 11!**

