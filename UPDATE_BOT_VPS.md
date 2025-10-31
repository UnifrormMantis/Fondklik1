# 🔄 ОБНОВЛЕНИЕ БОТА НА VPS

## ✅ ИСПРАВЛЕНИЕ:

Изменил вызов с `get_active_wallet()` на `get_payment_wallet(user_wallet)` чтобы использовать правильный эндпоинт `/get-payment-wallet`.

---

## 📋 ВЫПОЛНИТЕ НА VPS:

```bash
cd /opt/fondklik/bot

# Обновить код из GitHub
git pull

# Перезапустить бота
systemctl restart fondklik-bot.service

# Проверить статус
systemctl status fondklik-bot.service --no-pager -l | head -15

# Проверить логи
journalctl -u fondklik-bot.service -n 30 --no-pager | grep -i "кошелек\|payment\|error"
```

---

## 🧪 ПРОВЕРКА:

После обновления:

1. Откройте бот Fondklik в Telegram
2. Нажмите "Внести депозит" → "Оплатить"
3. **Должен показываться активный кошелек:** `TRpxhgJ9izoZ56iHJ6gkWwvuStaMeCTisS`
4. **НЕ должен показываться тестовый кошелек**

---

**Выполните команды на VPS!**

