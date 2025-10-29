#!/bin/bash

# Скрипт для остановки Telegram бота

echo "🛑 Остановка Telegram бота..."

# Останавливаем все процессы bot_final.py
BOT_PIDS=$(ps aux | grep "python3 bot_final.py" | grep -v grep | awk '{print $2}')

if [ ! -z "$BOT_PIDS" ]; then
    echo "🔄 Найдены процессы бота: $BOT_PIDS"
    echo "$BOT_PIDS" | xargs kill -TERM 2>/dev/null
    sleep 2
    
    # Проверяем, остановились ли процессы
    REMAINING_PIDS=$(ps aux | grep "python3 bot_final.py" | grep -v grep | awk '{print $2}')
    if [ ! -z "$REMAINING_PIDS" ]; then
        echo "🔄 Принудительная остановка..."
        echo "$REMAINING_PIDS" | xargs kill -9 2>/dev/null
        sleep 1
    fi
    
    echo "✅ Процессы бота остановлены"
else
    echo "ℹ️  Процессы бота не найдены"
fi

# Удаляем файл блокировки
if [ -f "bot.lock" ]; then
    rm -f bot.lock
    echo "🗑️  Файл блокировки удален"
fi

echo "🎉 Бот полностью остановлен"

















