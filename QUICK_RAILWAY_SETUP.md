# ⚡ Быстрый старт на Railway

## За 10 минут ваш бот будет работать 24/7!

### Шаг 1: GitHub (2 минуты)

```bash
# В терминале, в папке вашего проекта:
git init
git add .
git commit -m "Initial commit"
```

Создайте репозиторий на [github.com](https://github.com/new), затем:

```bash
git remote add origin https://github.com/ВАШ_USERNAME/fondklik-bot.git
git branch -M main
git push -u origin main
```

### Шаг 2: Railway (5 минут)

1. Откройте [railway.app](https://railway.app)
2. Войдите через GitHub
3. Нажмите **"New Project"**
4. Выберите **"Deploy from GitHub repo"**
5. Выберите ваш репозиторий `fondklik-bot`

### Шаг 3: Переменные окружения (3 минуты)

В Railway откройте ваш проект → **"Variables"** → добавьте:

```
TELEGRAM_BOT_TOKEN=8419656259:AAFkxcyrvb5mw4sHjelO42RZmrCvQtYOzYM
PAYMENT_API_KEY=rsG7Hzt0EaEY5ZoEH4eE96SiY234qpiSYg5d92xrSm4
TRON_API_URL=https://api.trongrid.io
```

### Шаг 4: Настройка сервисов

Railway автоматически создаст 2 сервиса из `Procfile`:

- **web** (Payment API)
- **bot** (Telegram Bot)

#### Для сервиса "web":
1. Откройте "Settings"
2. В "Networking" → включите **"Public Networking"**
3. Скопируйте полученный URL (типа `https://fondklik-bot-web.up.railway.app`)

#### Добавьте переменную для бота:
В "Variables" добавьте:
```
PAYMENT_API_URL=https://ваш-web-url.up.railway.app
```

### Шаг 5: Проверка

1. Откройте "Deployments" → выберите последний деплой
2. Нажмите "View Logs"
3. Убедитесь, что видите:
   - ✅ `Payment Bot найден` или `Используется Railway Payment API`
   - ✅ `Application started successfully`

### Готово! 🎉

Ваш бот работает 24/7 на Railway!

---

## Обновление кода

После любых изменений:

```bash
git add .
git commit -m "Описание изменений"
git push
```

Railway автоматически обновит бота!

---

## Полезные ссылки

- 📖 [Полная документация](./RAILWAY_DEPLOY_GUIDE.md)
- 🔧 [Railway Dashboard](https://railway.app/dashboard)
- 💬 [Telegram Bot](https://t.me/ваш_бот)

---

## Что делать если что-то не работает?

### Бот не отвечает
1. Проверьте логи сервиса "bot"
2. Убедитесь, что `TELEGRAM_BOT_TOKEN` правильный
3. Проверьте, что сервис запущен (зеленый статус)

### Payment API не работает
1. Проверьте логи сервиса "web"
2. Убедитесь, что Public Networking включен
3. Проверьте переменную `PAYMENT_API_URL` в боте

### База данных сбрасывается
Railway использует временное хранилище. Для постоянной БД:
1. Добавьте PostgreSQL сервис
2. Railway автоматически добавит `DATABASE_URL`
3. Обновите код для работы с PostgreSQL

---

## Стоимость

- **Бесплатно**: $5 в месяц
- Обычно хватает для небольшого бота с ~1000 пользователей
- Если закончится, просто обновите до Hobby плана ($5/месяц)

Удачи! 🚀

