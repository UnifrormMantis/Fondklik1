# 🔧 Исправление ошибки Payment Bot

## ❌ ОШИБКА:
```
PTBUserWarning: No `JobQueue` set up. To use `JobQueue`, you must install PTB via `pip install python-telegram-bot[job-queue]`.
❌ Критическая ошибка: 'NoneType' object has no attribute 'run_repeating'
```

## ✅ РЕШЕНИЕ:

Бот требует `python-telegram-bot[job-queue]` для работы с JobQueue.

### На VPS выполните:

```bash
cd /opt/fondklik/payment_bot
source venv/bin/activate

# Устанавливаем правильную версию с job-queue
pip install --upgrade "python-telegram-bot[job-queue]"

# Или переустановите все зависимости
pip install -r requirements.txt
pip install "python-telegram-bot[job-queue]"

deactivate

# Перезапускаем сервис
systemctl restart payment-bot.service
sleep 3

# Проверяем статус
systemctl status payment-bot.service --no-pager -l | head -20
```

---

## 🔄 АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ:

Если не нужен JobQueue, можно изменить код, но проще установить правильную зависимость.

---

**Выполните команды выше на VPS!**

