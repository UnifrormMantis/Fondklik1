# 🔧 ВОССТАНОВЛЕНИЕ ТЕРМИНАЛА

## ❗ ПРОБЛЕМА:
Терминал не отвечает (завис на `journalctl -f`)

---

## 📋 РЕШЕНИЕ:

### 1. Остановить зависшую команду:
```
Нажмите: Ctrl+C
(Если не помогает - Ctrl+Z, потом kill %1)
```

### 2. После остановки выполните:

```bash
cd /opt/fondklik/bot

# Обновить код из GitHub
git pull

# Установить python-dotenv если нужно
source venv/bin/activate
pip install python-dotenv 2>/dev/null || echo "Уже установлен"
deactivate

# Перезапустить бота
systemctl restart fondklik-bot.service
sleep 3

# Проверить статус (без -f!)
systemctl status fondklik-bot.service --no-pager -l | head -15
```

---

**Нажмите Ctrl+C в терминале чтобы остановить зависшую команду!**

