# ✅ ИСПРАВЛЕНИЕ PAYMENT_CLIENT НА VPS

## ❗ ПРОБЛЕМА:
PaymentClient не использует переменную окружения PAYMENT_API_URL если find_payment_bot() возвращает None

---

## 📋 ИСПРАВЛЕНИЕ НА VPS:

```bash
cd /opt/fondklik/bot

# 1. Обновить payment_client.py из GitHub
git pull

# 2. Или исправить вручную - добавить проверку переменной окружения
# Найти строку 80 в payment_client.py и изменить:
sed -i '80a\        # Если URL не найден и есть переменная окружения - используем её\n        if not self.api_url and PAYMENT_API_URL:\n            self.api_url = PAYMENT_API_URL\n            logger.info(f"✅ Используется Payment API из переменной окружения: {PAYMENT_API_URL}")' payment_client.py

# 3. Также исправить в методе get_payment_wallet (строка ~132):
# Добавить проверку PAYMENT_API_URL перед поиском
sed -i '/if not self.api_url:/a\            # Сначала пробуем переменную окружения\n            if PAYMENT_API_URL:\n                self.api_url = PAYMENT_API_URL' payment_client.py

# 4. Проверить что переменная окружения установлена
cat .env | grep PAYMENT_API_URL

# 5. Перезапустить
systemctl restart fondklik-bot.service
sleep 3

# 6. Проверить
systemctl status fondklik-bot.service --no-pager -l | head -10
```

---

**Или просто обновите из GitHub: `git pull`**

