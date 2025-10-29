# 🚀 Гайд по деплою на Railway.app

## Подготовка проекта

Ваш проект готов к деплою! Все необходимые файлы созданы:

- ✅ `requirements.txt` - зависимости Python
- ✅ `Procfile` - команды запуска для Railway
- ✅ `runtime.txt` - версия Python
- ✅ `.env.example` - пример переменных окружения
- ✅ Все необходимые файлы скопированы

## Шаг 1: Создание GitHub репозитория

### Вариант А: Через GitHub Desktop (проще)
1. Скачайте GitHub Desktop: https://desktop.github.com/
2. Откройте GitHub Desktop
3. `File → Add Local Repository` → выберите папку `1 пробник`
4. Создайте `.gitignore` файл (см. ниже)
5. Сделайте первый коммит: "Initial commit"
6. `Repository → Push to GitHub`

### Вариант Б: Через командную строку
```bash
# 1. Инициализируйте git репозиторий
git init

# 2. Создайте .gitignore файл
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/

# Databases
*.db
*.sqlite3

# Environment
.env
*.pid
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Backups
*_backup*.py
EOF

# 3. Добавьте файлы
git add .

# 4. Сделайте первый коммит
git commit -m "Initial commit: Telegram bot with payment API"

# 5. Создайте репозиторий на GitHub (через браузер на github.com)
# Затем подключите его:
git remote add origin https://github.com/ВАШ_USERNAME/ВАШ_РЕПОЗИТОРИЙ.git
git branch -M main
git push -u origin main
```

## Шаг 2: Деплой на Railway

### 1. Войдите в Railway
- Перейдите на https://railway.app
- Нажмите "Login" → войдите через GitHub

### 2. Создайте новый проект
1. Нажмите "New Project"
2. Выберите "Deploy from GitHub repo"
3. Выберите ваш репозиторий
4. Railway автоматически определит, что это Python проект

### 3. Настройте переменные окружения
1. В Railway откройте ваш проект
2. Перейдите в "Variables"
3. Добавьте следующие переменные:

```
TELEGRAM_BOT_TOKEN=8419656259:AAFkxcyrvb5mw4sHjelO42RZmrCvQtYOzYM
TRON_API_URL=https://api.trongrid.io
PAYMENT_API_KEY=rsG7Hzt0EaEY5ZoEH4eE96SiY234qpiSYg5d92xrSm4
DATABASE_URL=sqlite:///payments.db
CHECK_INTERVAL=60
CONFIRMATION_BLOCKS=3
```

### 4. Настройте два сервиса

Railway поддерживает несколько процессов из `Procfile`. Вам нужно:

1. В настройках проекта найдите "Services"
2. У вас должно быть два сервиса:
   - **web** (Payment API) - будет доступен по URL
   - **bot** (Telegram Bot) - работает в фоне

### 5. Важные настройки

#### Для Payment API (web):
- Port: Railway автоматически назначит порт через `$PORT`
- Public Networking: **Включите** (чтобы бот мог обращаться к API)

#### Для Telegram Bot (bot):
- Port: не требуется
- Public Networking: не требуется

## Шаг 3: После деплоя

### 1. Получите URL Payment API
После деплоя Railway даст вам URL типа:
```
https://your-project-name.up.railway.app
```

### 2. Обновите `payment_client.py`
Обновите `PAYMENT_PORTS` в файле `payment_client.py`:

```python
# Вместо портов, используйте Railway URL
PAYMENT_API_URL = "https://your-project-name.up.railway.app"
```

**ИЛИ** оставьте автопоиск - Railway будет работать на стандартном порту 80/443.

### 3. Проверьте логи
В Railway:
1. Откройте "Deployments"
2. Выберите последний деплой
3. Нажмите "View Logs"
4. Убедитесь, что оба сервиса запустились без ошибок

## Шаг 4: Обновление кода

После каждого изменения кода:

```bash
git add .
git commit -m "Описание изменений"
git push
```

Railway автоматически задеплоит новую версию!

## Troubleshooting (Решение проблем)

### Проблема: База данных не сохраняется
**Решение**: Railway предоставляет временное хранилище. Для постоянной БД:
1. В Railway добавьте "PostgreSQL" сервис
2. Railway автоматически создаст переменную `DATABASE_URL`
3. Обновите код для работы с PostgreSQL (см. ниже)

### Проблема: Бот не отвечает
**Проверьте**:
1. Логи бота в Railway
2. Правильность `TELEGRAM_BOT_TOKEN`
3. Что сервис "bot" запущен

### Проблема: Payment API недоступен
**Проверьте**:
1. Что Public Networking включен для "web" сервиса
2. URL Payment API правильный
3. Переменная `PAYMENT_API_KEY` совпадает в боте и API

## Переход на PostgreSQL (опционально, для продакшена)

Railway рекомендует использовать PostgreSQL вместо SQLite:

### 1. Добавьте PostgreSQL в проект
1. В Railway: "New" → "Database" → "Add PostgreSQL"
2. Railway автоматически создаст `DATABASE_URL`

### 2. Обновите requirements.txt
```
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
```

### 3. Обновите database.py
Замените `sqlite3` на SQLAlchemy с PostgreSQL.

## Мониторинг

### Просмотр логов в реальном времени
```bash
# Установите Railway CLI
npm install -g @railway/cli

# Войдите
railway login

# Подключитесь к проекту
railway link

# Смотрите логи
railway logs
```

## Полезные команды Railway CLI

```bash
# Статус проекта
railway status

# Переменные окружения
railway variables

# Открыть проект в браузере
railway open

# Локальный запуск с Railway переменными
railway run python3 bot_fondklik_correct.py
```

## Стоимость

- **Бесплатно**: $5 в месяц (обычно хватает для небольшого бота)
- **Hobby**: $5/месяц + использование
- **Pro**: $20/месяц + использование

Для начала бесплатных $5 должно хватить!

## Следующие шаги

После успешного деплоя:
1. ✅ Протестируйте бота
2. ✅ Проверьте работу платежей
3. ✅ Настройте мониторинг
4. ✅ Добавьте резервное копирование БД

Удачи! 🚀

