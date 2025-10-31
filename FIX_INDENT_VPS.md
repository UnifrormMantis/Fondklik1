# 🔧 ИСПРАВЛЕНИЕ ОТСТУПОВ НА VPS

## ❗ ПРОБЛЕМА:
`IndentationError: unexpected indent (bot_fondklik_correct.py, line 872)`

---

## 📋 ИСПРАВЛЕНИЕ НА VPS:

```bash
cd /opt/fondklik/bot

# 1. Посмотреть строки вокруг 872
sed -n '865,880p' bot_fondklik_correct.py

# 2. Проверить отступы
python3 -c "
with open('bot_fondklik_correct.py', 'r') as f:
    lines = f.readlines()
    for i in range(865, min(880, len(lines))):
        print(f'{i+1}: {repr(lines[i][:80])}')"

# 3. Исправить отступы (вероятно строка 872 имеет неправильный отступ)
# Проверим что там:
sed -n '870,875p' bot_fondklik_correct.py | cat -A

# 4. Если нужно откатить к рабочей версии из GitHub:
git checkout HEAD -- bot_fondklik_correct.py

# 5. Или исправить вручную - проверить контекст
sed -n '858,880p' bot_fondklik_correct.py

# 6. После исправления проверить синтаксис:
python3 -m py_compile bot_fondklik_correct.py

# 7. Перезапустить
systemctl restart fondklik-bot.service
```

---

**Сначала выполните команду 1 и 4 (откат), потом проверьте что код правильный!**

