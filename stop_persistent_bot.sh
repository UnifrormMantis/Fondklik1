#!/bin/bash

echo "🛑 Остановка бота для постоянной работы"
echo "======================================="

# Остановить бота
if [ -f "bot_persistent.pid" ]; then
    BOT_PID=$(cat bot_persistent.pid)
    echo "🛑 Остановка бота (PID: $BOT_PID)..."
    kill $BOT_PID 2>/dev/null
    rm -f bot_persistent.pid
    echo "✅ Бот остановлен"
else
    echo "ℹ️  PID файл бота не найден"
fi

# Остановить webhook сервер
if [ -f "webhook_server.pid" ]; then
    WEBHOOK_PID=$(cat webhook_server.pid)
    echo "🛑 Остановка webhook сервера (PID: $WEBHOOK_PID)..."
    kill $WEBHOOK_PID 2>/dev/null
    rm -f webhook_server.pid
    echo "✅ Webhook сервер остановлен"
else
    echo "ℹ️  PID файл webhook сервера не найден"
fi

# Дополнительная очистка
echo "🧹 Дополнительная очистка..."
pkill -f "python3 bot_final.py" 2>/dev/null
pkill -f "python3 webhook_server_standalone.py" 2>/dev/null

# Очистить lock файлы
rm -f bot.lock

echo "🎉 Все процессы остановлены"









