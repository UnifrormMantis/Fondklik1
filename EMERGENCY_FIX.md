# 🚨 СРОЧНОЕ ВОССТАНОВЛЕНИЕ БОТА

## ❗ БОТ НЕ РАБОТАЕТ

---

## 📋 ВЫПОЛНИТЕ НА VPS:

```bash
# 1. Проверить статус бота
systemctl status fondklik-bot.service --no-pager -l | head -20

# 2. Проверить последние логи с ошибками
journalctl -u fondklik-bot.service -n 100 --no-pager | grep -i "error\|exception\|traceback\|syntax\|indent" | tail -30

# 3. Проверить синтаксис Python файла
cd /opt/fondklik/bot
python3 -m py_compile bot_fondklik_correct.py 2>&1

# 4. Проверить последние логи полностью
journalctl -u fondklik-bot.service -n 50 --no-pager | tail -30

# 5. Если синтаксическая ошибка - откатить изменения
cd /opt/fondklik/bot
git log --oneline -5
git diff HEAD bot_fondklik_correct.py | head -50

# 6. Если нужно - откатить последний коммит
# git reset --hard HEAD~1
# systemctl restart fondklik-bot.service
```

---

**ВЫПОЛНИТЕ КОМАНДЫ 1-4 И ПРИШЛИТЕ РЕЗУЛЬТАТЫ!**

