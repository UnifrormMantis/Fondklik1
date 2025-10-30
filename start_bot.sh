#!/bin/bash
# Скрипт для безопасного запуска FondKlik Bot

echo "🤖 Запуск FondKlik Telegram бота..."

# Проверяем .env
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден! Создайте его на основе .env.example"
    exit 1
fi

# Загружаем переменные окружения
set -a
source .env
set +a

# Проверяем токен
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN не установлен в .env"
    exit 1
fi

# Проверяем, не запущен ли уже бот
if [ -f "bot.lock" ]; then
    echo "⚠️  Обнаружен файл блокировки bot.lock"
    echo "🔄 Попытка остановки предыдущего экземпляра..."
    
    pkill -f "python3 bot_fondklik_correct.py" 2>/dev/null
    sleep 3
    
    rm -f bot.lock
    echo "🗑️  Файл блокировки удален"
fi

echo "🔄 Сброс Telegram API webhook..."
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook" > /dev/null
sleep 2

echo "🚀 Запуск бота..."
python3 bot_fondklik_correct.py &

echo "🔍 Проверка запуска..."
sleep 3

# Проверяем, что бот запустился
if [ -f "bot.lock" ]; then
    BOT_PID=$(ps aux | grep "python3 bot_fondklik_correct.py" | grep -v grep | awk '{print $2}')
    if [ ! -z "$BOT_PID" ]; then
        echo "✅ Бот успешно запущен (PID: $BOT_PID)"
        echo "🔒 Блокировка активна - повторный запуск невозможен"
        echo "🎉 Готово! Бот работает."
    else
        echo "❌ Ошибка запуска бота"
        rm -f bot.lock
        exit 1
    fi
else
    echo "⚠️  Бот запущен, но блокировка не создана (возможно, бот уже работает)"
fi
