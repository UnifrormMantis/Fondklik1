# 🔧 Команды для добавления админа 8489431460

## На VPS выполните все команды:

```bash
cd /opt/fondklik/payment_bot

# 1. Добавить в whitelist
source venv/bin/activate
python manage_whitelist.py add 8489431460
deactivate

# 2. Изменить ID админа в коде (в трех местах)
sed -i 's/if user_id not in \[123456789\]/if user_id not in [8489431460]/g' private_bot.py

# 3. Проверить изменения
grep -n "if user_id not in" private_bot.py

# 4. Перезапустить бота
systemctl restart payment-bot.service
sleep 3

# 5. Проверить статус
systemctl status payment-bot.service --no-pager -l | head -10
```

---

## Или одной командой:

```bash
cd /opt/fondklik/payment_bot && \
source venv/bin/activate && \
python manage_whitelist.py add 8489431460 && \
deactivate && \
sed -i 's/if user_id not in \[123456789\]/if user_id not in [8489431460]/g' private_bot.py && \
systemctl restart payment-bot.service && \
sleep 3 && \
systemctl status payment-bot.service --no-pager -l | head -10
```

---

## После этого:

Пользователь `8489431460` сможет использовать:
- `/admin_add_user <user_id>` - добавить пользователя
- `/admin_remove_user <user_id>` - удалить пользователя
- `/admin_list_users` - список пользователей

---

**Выполните команды на VPS!**

