#!/bin/bash

# Скрипт для безопасного запуска Telegram бота
# Использует встроенную систему блокировки для предотвращения множественного запуска

echo "🤖 Запуск Telegram бота с системой блокировки..."

# Проверяем, не запущен ли уже бот
if [ -f "bot.lock" ]; then
    echo "⚠️  Обнаружен файл блокировки bot.lock"
    echo "🔄 Попытка остановки предыдущего экземпляра..."
    
    # Останавливаем все процессы bot_final.py
    pkill -f "python3 bot_final.py" 2>/dev/null
    sleep 3
    
    # Удаляем файл блокировки
    rm -f bot.lock
    echo "🗑️  Файл блокировки удален"
fi

echo "🔄 Сброс Telegram API..."
curl -s -X POST "https://api.telegram.org/bot8204117323:AAEe4-1jEKpSkpr13-FYjdSdFeBdbQHpNcY/deleteWebhook" > /dev/null
sleep 2

echo "🚀 Запуск бота..."
python3 bot_final.py &

echo "🔍 Проверка запуска..."
sleep 3

# Проверяем, что бот запустился
if [ -f "bot.lock" ]; then
    BOT_PID=$(ps aux | grep "python3 bot_final.py" | grep -v grep | awk '{print $2}')
    if [ ! -z "$BOT_PID" ]; then
        echo "✅ Бот успешно запущен (PID: $BOT_PID)"
        echo "🔒 Блокировка активна - повторный запуск невозможен"
        echo "📊 Статус процессов:"
        ps aux | grep python | grep -v grep
        echo "🎉 Готово! Бот работает без конфликтов."
    else
        echo "❌ Ошибка запуска бота"
        rm -f bot.lock
        exit 1
    fi
else
    echo "❌ Бот не смог получить блокировку"
    echo "🔍 Возможно, другой экземпляр уже запущен"
    exit 1
fi
