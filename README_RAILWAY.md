# 💰 ФондКлик - Telegram Crypto Investment Bot

Платформа для управления краткосрочными депозитами с фиксированным доходом в USDT (TRC20).

## 🚀 Возможности

- 💸 **Депозиты с фиксированной доходностью**
  - 10-дневные: 8% доходности
  - 30-дневные: 30% доходности

- 👥 **3-уровневая реферальная система**
  - 1-й уровень: 15% (30 дней) / 5% (10 дней)
  - 2-й уровень: 10% (30 дней) / 3% (10 дней)
  - 3-й уровень: 5% (30 дней) / 1.5% (10 дней)

- 🔄 **Автоматическая обработка платежей**
  - Интеграция с TRON API
  - Автоматическая проверка транзакций
  - Динамическое управление кошельками

- 👨‍💼 **Админ-панель**
  - Управление депозитами
  - Статистика пользователей
  - Настройка кошельков

## 📦 Технологии

- **Backend**: Python 3.11+
- **Bot Framework**: python-telegram-bot 20.7
- **Payment API**: FastAPI + Uvicorn
- **Blockchain**: TRON (TRC20 USDT)
- **Database**: SQLite (можно PostgreSQL)
- **Hosting**: Railway.app

## ⚡ Быстрый старт

### Локальный запуск

```bash
# Установите зависимости
pip install -r requirements.txt

# Настройте переменные окружения
cp env_example.txt .env
# Отредактируйте .env, добавив ваш TELEGRAM_BOT_TOKEN

# Запустите Payment API
python3 simple_payment_api.py

# В другом терминале запустите бота
python3 bot_fondklik_correct.py
```

### Деплой на Railway

📖 [Полная инструкция](./QUICK_RAILWAY_SETUP.md)

**Кратко:**
1. Создайте GitHub репозиторий
2. Подключите к Railway
3. Добавьте переменные окружения
4. Готово! 🎉

## 📁 Структура проекта

```
├── bot_fondklik_correct.py    # Основной бот
├── simple_payment_api.py      # Payment Bot API
├── payment_client.py          # Клиент для Payment API
├── payment_handlers.py        # Обработчики платежей
├── database.py                # Работа с БД
├── tron_tracker.py            # Отслеживание TRON транзакций
├── config.py                  # Конфигурация
├── Procfile                   # Конфигурация Railway
├── requirements.txt           # Зависимости
└── README.md                  # Документация
```

## 🔧 Конфигурация

### Обязательные переменные окружения

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
PAYMENT_API_KEY=your_payment_api_key
```

### Опциональные переменные

```bash
TRON_API_URL=https://api.trongrid.io
TRON_API_KEY=your_tron_api_key
PAYMENT_API_URL=http://localhost:8001  # Для Railway
DATABASE_URL=sqlite:///bot_database.db
```

## 📊 Функциональность

### Для пользователей:
- ✅ Создание депозитов
- ✅ Просмотр активных депозитов
- ✅ Реферальная программа
- ✅ История транзакций
- ✅ Настройка кошелька USDT

### Для администраторов:
- ✅ Управление депозитами пользователей
- ✅ Создание тестовых депозитов
- ✅ Статистика платформы
- ✅ Управление активными кошельками
- ✅ Просмотр логов

## 🔐 Безопасность

- 🔒 Хеширование API ключей
- 🔒 Проверка транзакций через TRON API
- 🔒 Защита от дублирования депозитов
- 🔒 Блокировка множественного запуска бота

## 📈 Мониторинг

Просмотр логов:
```bash
# Локально
tail -f bot.log

# На Railway
railway logs --service bot
```

## 🤝 Поддержка

Для вопросов и предложений:
- 📧 Email: support@fondklik.com
- 💬 Telegram: @fondklik_support

## 📄 Лицензия

Proprietary - Все права защищены

---

**Сделано с ❤️ для криптосообщества**

