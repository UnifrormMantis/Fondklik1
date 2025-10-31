# 🔧 Восстановление админки Payment Bot

## ❌ ПРОБЛЕМА:

В коде админ ID захардкожен как `123456789` (пример). Нужно:
1. Добавить вас в whitelist
2. Изменить ID админа в коде

---

## ✅ РЕШЕНИЕ 1: Добавить через manage_whitelist.py (БЫСТРО)

### На VPS выполните:

```bash
cd /opt/fondklik/payment_bot
source venv/bin/activate

# Добавить себя в whitelist (замените YOUR_USER_ID на ваш Telegram ID)
python manage_whitelist.py add YOUR_USER_ID

# Проверить список
python manage_whitelist.py list

deactivate
```

**Как узнать свой Telegram ID:**
1. Напишите боту @userinfobot в Telegram
2. Он покажет ваш ID

---

## ✅ РЕШЕНИЕ 2: Изменить ID админа в коде

### На VPS:

```bash
cd /opt/fondklik/payment_bot

# Найти и заменить ID админа
# Замените YOUR_ADMIN_ID на ваш реальный Telegram ID
sed -i 's/if user_id not in \[123456789\]/if user_id not in [YOUR_ADMIN_ID]/g' private_bot.py

# Проверить изменения
grep -n "if user_id not in" private_bot.py

# Перезапустить бота
systemctl restart payment-bot.service
```

---

## ✅ РЕШЕНИЕ 3: Добавить напрямую в базу данных

```bash
cd /opt/fondklik/payment_bot
source venv/bin/activate
python3 <<EOF
from database import Database
db = Database()
# Замените YOUR_USER_ID на ваш Telegram ID
db.add_user(YOUR_USER_ID, "your_username", "")
print(f"✅ Пользователь {YOUR_USER_ID} добавлен")
EOF
deactivate

# Перезапустить бота
systemctl restart payment-bot.service
```

---

## 🔍 КАК УЗНАТЬ СВОЙ TELEGRAM ID:

1. Напишите боту **@userinfobot** в Telegram
2. Он покажет ваш ID (например: `123456789`)

Или:

1. Напишите боту **@getidsbot**
2. Он тоже покажет ваш ID

---

## 📋 ПОСЛЕ ВОССТАНОВЛЕНИЯ:

В Payment Bot будут доступны команды:
- `/admin_add_user <user_id>` - добавить пользователя в whitelist
- `/admin_remove_user <user_id>` - удалить пользователя
- `/admin_list_users` - список пользователей в whitelist

---

**Сначала выполните Решение 1 или 3, чтобы добавить себя в whitelist!**

