# ⚡ Шпаргалка по командам

## 🚀 Быстрый старт

### Автоматическая инициализация git
```bash
./init_git.sh
```

### Ручная инициализация git
```bash
git init
git add .
git commit -m "Initial commit: Ready for Railway"
git remote add origin https://github.com/ВАШ_USERNAME/fondklik-bot.git
git branch -M main
git push -u origin main
```

---

## 🔧 Локальный запуск (для тестирования)

### Запустить Payment API
```bash
python3 simple_payment_api.py
```

### Запустить бота (в другом терминале)
```bash
python3 bot_fondklik_correct.py
```

### Проверить модули
```bash
python3 -c "import payment_client, database, tron_tracker, config; print('✅ OK')"
```

---

## 📦 Git команды

### Обновить код на Railway
```bash
git add .
git commit -m "Описание изменений"
git push
```

### Проверить статус
```bash
git status
```

### Посмотреть логи
```bash
git log --oneline
```

### Отменить последний коммит (если нужно)
```bash
git reset --soft HEAD~1
```

---

## 🚂 Railway CLI (опционально)

### Установить Railway CLI
```bash
npm install -g @railway/cli
```

### Войти в Railway
```bash
railway login
```

### Подключиться к проекту
```bash
railway link
```

### Просмотр логов
```bash
# Логи бота
railway logs --service bot

# Логи Payment API
railway logs --service web

# Все логи в реальном времени
railway logs --follow
```

### Проверить переменные окружения
```bash
railway variables
```

### Локальный запуск с Railway переменными
```bash
railway run python3 bot_fondklik_correct.py
```

### Открыть проект в браузере
```bash
railway open
```

---

## 🔍 Проверка и отладка

### Проверить синтаксис Python
```bash
python3 -m py_compile bot_fondklik_correct.py
python3 -m py_compile simple_payment_api.py
```

### Проверить зависимости
```bash
pip install -r requirements.txt --dry-run
```

### Посмотреть логи бота (локально)
```bash
tail -f bot.log
```

### Проверить Payment API
```bash
curl http://localhost:8001/health
```

### Получить активный кошелек
```bash
curl -X POST http://localhost:8001/get-payment-wallet \
  -H "X-API-Key: rsG7Hzt0EaEY5ZoEH4eE96SiY234qpiSYg5d92xrSm4" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "test"}'
```

---

## 📊 Мониторинг

### Проверить запущенные процессы
```bash
ps aux | grep python
```

### Убить зависший процесс
```bash
pkill -f bot_fondklik_correct.py
pkill -f simple_payment_api.py
```

### Проверить порты
```bash
lsof -i :8001  # Payment API
```

---

## 🗄️ База данных

### Открыть SQLite консоль
```bash
sqlite3 bot_database.db
```

### Посмотреть таблицы
```sql
.tables
```

### Посмотреть пользователей
```sql
SELECT * FROM users;
```

### Посмотреть депозиты
```sql
SELECT * FROM deposits;
```

### Выйти из SQLite
```sql
.quit
```

---

## 🧹 Очистка

### Удалить временные файлы
```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete
```

### Удалить логи (будьте осторожны!)
```bash
rm -f *.log
```

### Удалить lock файлы
```bash
rm -f bot.lock *.pid
```

---

## 📝 Переменные окружения для Railway

Добавьте эти переменные в Railway → Variables:

```bash
TELEGRAM_BOT_TOKEN=8419656259:AAFkxcyrvb5mw4sHjelO42RZmrCvQtYOzYM
PAYMENT_API_KEY=rsG7Hzt0EaEY5ZoEH4eE96SiY234qpiSYg5d92xrSm4
TRON_API_URL=https://api.trongrid.io
PAYMENT_API_URL=https://ваш-web-сервис.up.railway.app
```

---

## 🆘 Полезные ссылки

- 🚂 Railway Dashboard: https://railway.app/dashboard
- 🐙 GitHub: https://github.com
- 📚 Railway Docs: https://docs.railway.app
- 🐍 Python Docs: https://docs.python.org
- 💬 Telegram Bot API: https://core.telegram.org/bots/api

---

## 💡 Советы

### Перед деплоем
1. Протестируйте локально
2. Проверьте все зависимости
3. Убедитесь что .gitignore настроен
4. Не коммитьте `.env`, `.db`, `.log` файлы

### После деплоя
1. Проверьте логи в Railway
2. Протестируйте бота в Telegram
3. Мониторьте использование ресурсов
4. Настройте резервное копирование БД

### При ошибках
1. Читайте логи: `railway logs`
2. Проверяйте переменные окружения
3. Запускайте локально для отладки
4. Проверяйте документацию в START_HERE.md

---

**Удачи! 🚀**

