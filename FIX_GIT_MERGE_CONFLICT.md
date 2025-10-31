# 🔧 Исправление конфликта при обновлении

## ❌ ПРОБЛЕМА:
```
error: Your local changes to the following files would be overwritten by merge:
	private_bot.py
```

## ✅ РЕШЕНИЕ: Сохранить локальные изменения и обновить

### На VPS выполните:

```bash
cd /opt/fondklik/payment_bot

# 1. Сохранить локальные изменения (админ ID)
git stash

# 2. Обновить из GitHub
git pull

# 3. Вернуть локальные изменения
git stash pop

# 4. Если будут конфликты - решить их:
# (в файле private_bot.py должны остаться ваши изменения админа)
```

---

## 🔄 АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ: Принудительное обновление

Если локальные изменения не важны (только админ ID):

```bash
cd /opt/fondklik/payment_bot

# Отменить локальные изменения
git reset --hard origin/main

# Или обновить принудительно
git fetch origin
git reset --hard origin/main

# Перезапустить бота
systemctl restart payment-bot.service
```

**После этого нужно будет СНОВА изменить админ ID:**

```bash
# Изменить админ ID на 8489431460
sed -i 's/if user_id not in \[123456789\]/if user_id not in [8489431460]/g' private_bot.py

# Перезапустить
systemctl restart payment-bot.service
```

---

## ✅ РЕКОМЕНДУЕМОЕ РЕШЕНИЕ:

```bash
cd /opt/fondklik/payment_bot

# 1. Посмотреть что изменилось локально
git diff private_bot.py

# 2. Сохранить изменения (stash)
git stash save "Local admin ID changes"

# 3. Обновить из GitHub
git pull

# 4. Вернуть изменения
git stash pop

# 5. Если есть конфликты - решить вручную или просто заменить админ ID
# Проверить что админ ID правильный
grep -n "if user_id not in" private_bot.py | head -3

# Если не правильный - исправить
sed -i 's/if user_id not in \[123456789\]/if user_id not in [8489431460]/g' private_bot.py

# 6. Перезапустить
systemctl restart payment-bot.service
```

---

**Выполните рекомендованные команды на VPS!**

