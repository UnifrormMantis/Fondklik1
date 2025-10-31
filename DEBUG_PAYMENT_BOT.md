# 🐛 Отладка Payment Bot

## ❌ Ошибка: `status=1/FAILURE`

Нужно посмотреть логи для выяснения причины.

---

## 🔍 КОМАНДЫ ДЛЯ ДИАГНОСТИКИ:

### На VPS выполните:

```bash
# 1. Просмотр логов сервиса
journalctl -u payment-bot.service -n 50 --no-pager

# 2. Просмотр логов из файлов
tail -50 /opt/fondklik/logs/payment-bot.log
tail -50 /opt/fondklik/logs/payment-bot-error.log

# 3. Попробовать запустить вручную для диагностики
cd /opt/fondklik/payment_bot
source venv/bin/activate
python main.py
# (Это покажет ошибку прямо в терминале)
```

---

## 🔧 ВОЗМОЖНЫЕ ПРИЧИНЫ:

1. **Неправильный токен или токен не установлен**
   - Проверьте: `cat /opt/fondklik/payment_bot/.env`

2. **Отсутствуют зависимости**
   - Проверьте: `cd /opt/fondklik/payment_bot && source venv/bin/activate && pip list`

3. **Проблемы с базой данных**
   - Файл `database.py` может требовать настройки

4. **Отсутствуют файлы конфигурации**
   - Проверьте наличие: `config.py`, `database.py`, `tron_tracker.py`

5. **Проблемы с импортами**
   - Некоторые модули могут отсутствовать

---

**Выполните команды выше и пришлите вывод логов!**

