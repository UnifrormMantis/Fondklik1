#!/bin/bash

echo "📊 Статус бота с webhook сервером"
echo "================================="

# Проверить бота
if [ -f "bot_with_webhook.pid" ]; then
    BOT_PID=$(cat bot_with_webhook.pid)
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo "✅ Бот работает (PID: $BOT_PID)"
    else
        echo "❌ Бот не работает (PID файл есть, но процесс не найден)"
        rm -f bot_with_webhook.pid
    fi
else
    echo "❌ Бот не запущен (PID файл не найден)"
fi

# Проверить webhook сервер
if [ -f "webhook_server.pid" ]; then
    WEBHOOK_PID=$(cat webhook_server.pid)
    if ps -p $WEBHOOK_PID > /dev/null 2>&1; then
        echo "✅ Webhook сервер работает (PID: $WEBHOOK_PID)"
    else
        echo "❌ Webhook сервер не работает (PID файл есть, но процесс не найден)"
        rm -f webhook_server.pid
    fi
else
    echo "❌ Webhook сервер не запущен (PID файл не найден)"
fi

# Проверить webhook endpoint
echo ""
echo "🔗 Проверка webhook endpoint..."
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Webhook endpoint доступен"
    echo "📡 Ответ:"
    curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8001/health
else
    echo "❌ Webhook endpoint недоступен"
fi

echo ""
echo "💡 Для запуска: ./start_bot_with_webhook.sh"
echo "💡 Для остановки: ./stop_bot_with_webhook.sh"
echo "💡 Для тестирования: python3 test_webhook_simulation.py"










