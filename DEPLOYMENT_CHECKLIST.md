# ✅ Чек-лист деплоя на Railway

## Подготовка завершена! ✅

Ваш проект готов к деплою. Все файлы созданы:

### Конфигурационные файлы:
- ✅ `Procfile` - команды запуска для Railway
- ✅ `requirements.txt` - Python зависимости
- ✅ `runtime.txt` - версия Python (3.11.0)
- ✅ `.gitignore` - игнорируемые файлы для git
- ✅ `env_example.txt` - пример переменных окружения

### Основной код:
- ✅ `bot_fondklik_correct.py` - обновлен для Railway
- ✅ `simple_payment_api.py` - обновлен для Railway
- ✅ `payment_client.py` - поддержка Railway URL
- ✅ `database.py` - работа с БД
- ✅ `tron_tracker.py` - отслеживание транзакций
- ✅ `config.py` - конфигурация
- ✅ `payment_handlers.py` - обработка платежей

### Документация:
- ✅ `QUICK_RAILWAY_SETUP.md` - быстрый старт
- ✅ `RAILWAY_DEPLOY_GUIDE.md` - полная инструкция
- ✅ `README_RAILWAY.md` - README для GitHub
- ✅ `DEPLOYMENT_CHECKLIST.md` - этот файл

---

## Что делать дальше:

### 1️⃣ Создать GitHub репозиторий (5 минут)

```bash
# Инициализируйте git
git init

# Добавьте все файлы
git add .

# Сделайте первый коммит
git commit -m "Initial commit: Ready for Railway deployment"

# Создайте репозиторий на github.com, затем:
git remote add origin https://github.com/ВАШ_USERNAME/fondklik-bot.git
git branch -M main
git push -u origin main
```

### 2️⃣ Деплой на Railway (5 минут)

1. Откройте https://railway.app
2. Login → GitHub
3. New Project → Deploy from GitHub repo
4. Выберите `fondklik-bot`

### 3️⃣ Настроить переменные окружения (2 минуты)

В Railway → Variables → добавьте:

```
TELEGRAM_BOT_TOKEN=8419656259:AAFkxcyrvb5mw4sHjelO42RZmrCvQtYOzYM
PAYMENT_API_KEY=rsG7Hzt0EaEY5ZoEH4eE96SiY234qpiSYg5d92xrSm4
TRON_API_URL=https://api.trongrid.io
```

### 4️⃣ Включить Public Networking для Payment API (1 минута)

1. Откройте сервис "web"
2. Settings → Networking → включите "Public Networking"
3. Скопируйте URL (например: `https://fondklik-web.up.railway.app`)
4. Добавьте переменную:
   ```
   PAYMENT_API_URL=ваш_скопированный_URL
   ```

### 5️⃣ Проверить деплой (2 минуты)

1. Deployments → View Logs
2. Убедитесь, что оба сервиса запустились:
   - ✅ `web` (Payment API)
   - ✅ `bot` (Telegram Bot)

---

## Важные замечания:

### 🔄 База данных
SQLite на Railway использует **временное хранилище**. Данные могут сбрасываться при редеплое.

**Для продакшена рекомендуется PostgreSQL:**
1. В Railway: New → Database → PostgreSQL
2. Railway автоматически добавит `DATABASE_URL`
3. Обновите код для работы с PostgreSQL

### 🔐 Секреты
- **НЕ** коммитьте `.env` файл в git
- Все секреты храните в Railway Variables
- Файл `env_example.txt` - только как пример

### 💰 Стоимость
- Бесплатно: $5/месяц (хватает для начала)
- При превышении: Hobby план $5/месяц

---

## Проверка работы:

### Локально (перед деплоем):
```bash
# Проверьте Payment API
curl http://localhost:8001/health

# Проверьте переменные окружения
echo $TELEGRAM_BOT_TOKEN
```

### На Railway:
```bash
# Установите Railway CLI (опционально)
npm install -g @railway/cli

# Войдите и подключитесь
railway login
railway link

# Просмотр логов
railway logs --service bot
railway logs --service web
```

---

## Troubleshooting:

### ❌ Ошибка: "Module not found"
Проверьте `requirements.txt` - все зависимости указаны

### ❌ Бот не отвечает
1. Проверьте логи сервиса "bot"
2. Убедитесь что `TELEGRAM_BOT_TOKEN` правильный
3. Проверьте что сервис запущен

### ❌ Payment API не найден
1. Проверьте Public Networking включен
2. Проверьте переменную `PAYMENT_API_URL`
3. Проверьте логи сервиса "web"

---

## Следующие шаги после деплоя:

1. ✅ Протестируйте бота в Telegram
2. ✅ Создайте тестовый депозит
3. ✅ Проверьте реферальную систему
4. ✅ Настройте мониторинг
5. ✅ Добавьте PostgreSQL для постоянного хранения
6. ✅ Настройте резервное копирование

---

## Полезные ссылки:

- 📖 [Быстрый старт](./QUICK_RAILWAY_SETUP.md)
- 📚 [Полная инструкция](./RAILWAY_DEPLOY_GUIDE.md)
- 🐙 [GitHub](https://github.com)
- 🚂 [Railway Dashboard](https://railway.app/dashboard)
- 📘 [Railway Docs](https://docs.railway.app)

---

**Удачи с деплоем! 🚀**

Если возникнут вопросы - проверьте логи в Railway или запустите локально для отладки.

