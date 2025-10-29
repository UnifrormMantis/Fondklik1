# 🎯 НАЧНИТЕ ОТСЮДА

## Ваш бот готов к деплоу на Railway! 🚀

Все необходимые файлы созданы и настроены для работы на Railway.app с **бесплатным первым месяцем** ($5 кредитов).

---

## ⚡ Быстрый старт (10 минут)

### Вариант 1: Автоматический (рекомендуется)

Просто запустите скрипт:

```bash
./init_git.sh
```

Скрипт автоматически:
- ✅ Инициализирует git
- ✅ Добавит нужные файлы
- ✅ Создаст первый коммит
- ✅ Покажет инструкции по GitHub

### Вариант 2: Ручной

```bash
git init
git add .
git commit -m "Initial commit"
```

Затем создайте репозиторий на [github.com](https://github.com/new) и:

```bash
git remote add origin https://github.com/ВАШ_USERNAME/fondklik-bot.git
git branch -M main
git push -u origin main
```

---

## 📚 Документация

Выберите нужную инструкцию:

### 🚀 Для быстрого деплоя:
👉 **[QUICK_RAILWAY_SETUP.md](./QUICK_RAILWAY_SETUP.md)** - 10 минут до запуска

### 📖 Для подробного изучения:
👉 **[RAILWAY_DEPLOY_GUIDE.md](./RAILWAY_DEPLOY_GUIDE.md)** - полная документация

### ✅ Контрольный список:
👉 **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** - что и как делать

### 📝 Для GitHub:
👉 **[README_RAILWAY.md](./README_RAILWAY.md)** - описание проекта

---

## 🎯 Пошаговый план

### Шаг 1: GitHub (5 мин)
```bash
./init_git.sh  # или вручную
```

### Шаг 2: Railway (3 мин)
1. Откройте [railway.app](https://railway.app)
2. Login через GitHub
3. New Project → Deploy from GitHub repo
4. Выберите ваш репозиторий

### Шаг 3: Переменные (2 мин)
Добавьте в Railway → Variables:
```
TELEGRAM_BOT_TOKEN=8419656259:AAFkxcyrvb5mw4sHjelO42RZmrCvQtYOzYM
PAYMENT_API_KEY=rsG7Hzt0EaEY5ZoEH4eE96SiY234qpiSYg5d92xrSm4
TRON_API_URL=https://api.trongrid.io
```

### Шаг 4: Настройка (1 мин)
- В сервисе "web": включите Public Networking
- Скопируйте URL и добавьте переменную:
  ```
  PAYMENT_API_URL=ваш_url_здесь
  ```

### Шаг 5: Готово! ✨
Проверьте логи → бот работает 24/7!

---

## 🔧 Что было сделано

### Файлы конфигурации:
- ✅ `Procfile` - запуск на Railway
- ✅ `requirements.txt` - зависимости Python
- ✅ `runtime.txt` - версия Python 3.11
- ✅ `.gitignore` - исключения для git

### Обновлен код:
- ✅ `bot_fondklik_correct.py` - читает токен из ENV
- ✅ `simple_payment_api.py` - читает PORT из ENV
- ✅ `payment_client.py` - поддержка Railway URL

### Скопированы из платежки:
- ✅ `database.py` - работа с БД
- ✅ `tron_tracker.py` - TRON транзакции
- ✅ `config.py` - конфигурация

### Документация:
- ✅ Быстрый старт
- ✅ Полная инструкция
- ✅ README для GitHub
- ✅ Чек-лист деплоя
- ✅ Этот файл 😊

---

## ⚠️ Важно знать

### База данных
SQLite на Railway - **временное хранилище**. Для продакшена:
1. Добавьте PostgreSQL в Railway
2. Railway автоматически настроит `DATABASE_URL`
3. Обновите код (инструкции в документации)

### Стоимость
- **$5 бесплатно** каждый месяц
- Хватает для ~1000 активных пользователей
- При превышении: $5/месяц

### Безопасность
- ❌ НЕ коммитьте файлы `.env`, `.db`, `.log`
- ✅ Все секреты храните в Railway Variables
- ✅ `.gitignore` уже настроен правильно

---

## 💡 Полезные команды

### Локальный запуск (тестирование):
```bash
# Payment API
python3 simple_payment_api.py

# В другом терминале - бот
python3 bot_fondklik_correct.py
```

### Git команды:
```bash
# Обновить код на Railway
git add .
git commit -m "Update: описание изменений"
git push

# Railway автоматически задеплоит!
```

### Railway CLI (опционально):
```bash
# Установка
npm install -g @railway/cli

# Просмотр логов
railway logs --service bot
railway logs --service web
```

---

## 🆘 Помощь

### Что-то не работает?

1. **Проверьте логи** в Railway (Deployments → View Logs)
2. **Проверьте переменные** окружения
3. **Запустите локально** для отладки
4. **Читайте документацию** в этой папке

### Типичные проблемы:

❓ **Бот не отвечает**
→ Проверьте `TELEGRAM_BOT_TOKEN` в Variables

❓ **Payment API не найден**
→ Включите Public Networking для "web" сервиса

❓ **База данных сбрасывается**
→ Используйте PostgreSQL вместо SQLite

---

## 🎉 После деплоя

Когда бот работает на Railway:

1. ✅ Протестируйте все функции
2. ✅ Создайте тестовый депозит
3. ✅ Проверьте реферальную систему
4. ✅ Добавьте PostgreSQL
5. ✅ Настройте резервное копирование
6. ✅ Мониторьте логи первые дни

---

## 📞 Контакты

- 📚 Документация: в этой папке
- 🚂 Railway: https://railway.app
- 🐙 GitHub: https://github.com

---

**Готовы начать? Запустите:**

```bash
./init_git.sh
```

**Или читайте:**
- [QUICK_RAILWAY_SETUP.md](./QUICK_RAILWAY_SETUP.md) - быстрый старт
- [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) - детальный чек-лист

---

**Удачи с деплоем! 🚀**

Через 10 минут ваш бот будет работать 24/7 на Railway!

