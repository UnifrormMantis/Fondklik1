# 🔍 ПРОВЕРКА ЛОГОВ ОШИБОК

## 📋 ВЫПОЛНИТЕ НА VPS ПОСЛЕ НАЖАТИЯ КНОПКИ "ОПЛАТИТЬ":

```bash
# 1. Проверить последние логи бота (в реальном времени)
journalctl -u fondklik-bot.service -n 100 --no-pager | tail -50

# 2. Проверить логи с ошибками и исключениями
journalctl -u fondklik-bot.service -n 200 --no-pager | grep -i "error\|exception\|traceback\|ошибка\|failed\|failed" | tail -30

# 3. Проверить файловые логи (если есть)
tail -50 /opt/fondklik/logs/bot.log 2>/dev/null || echo "Файл логов не найден"
tail -50 /opt/fondklik/logs/bot-error.log 2>/dev/null || echo "Файл ошибок не найден"

# 4. Проверить что код правильный - найти строку с ошибкой
grep -n "Произошла ошибка\|❌ Произошла ошибка" /opt/fondklik/bot/bot_fondklik_correct.py

# 5. Проверить что payment_client правильно импортируется
python3 -c "import sys; sys.path.insert(0, '/opt/fondklik/bot'); from payment_client import payment_client; print('OK')" 2>&1

# 6. Проверить что метод get_payment_wallet существует
python3 -c "import sys; sys.path.insert(0, '/opt/fondklik/bot'); from payment_client import payment_client; print(hasattr(payment_client, 'get_payment_wallet'))" 2>&1

# 7. Проверить переменные окружения
cat /opt/fondklik/bot/.env | grep PAYMENT
```

---

**Сначала выполните шаги 1 и 2 - там должна быть реальная ошибка!**
**После этого пришлите вывод этих команд.**

