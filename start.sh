#!/bin/bash
# Запуск FondKlik Bot

echo "🚀 Запуск FondKlik Bot..."

# Проверяем наличие .env
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден!"
    echo "Создайте .env файл на основе .env.example"
    exit 1
fi

# Загружаем переменные окружения
set -a
source .env
set +a

# Проверяем токен бота
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN не установлен в .env"
    exit 1
fi

# Останавливаем старые процессы если есть
pkill -f "python3 bot_fondklik_correct.py" 2>/dev/null
sleep 2

# Запускаем бота
echo "✅ Запускаем бота..."
python3 bot_fondklik_correct.py
