#!/bin/bash

echo "📊 Статус бота для постоянной работы"
echo "===================================="

# Проверить бота
if [ -f "bot_persistent.pid" ]; then
    BOT_PID=$(cat bot_persistent.pid)
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo "✅ Бот работает (PID: $BOT_PID)"
    else
        echo "❌ Бот не работает (PID файл есть, но процесс не найден)"
        rm -f bot_persistent.pid
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

# Показать последние логи
echo ""
echo "📝 Последние логи бота:"
if [ -f "bot.log" ]; then
    echo "--- bot.log (последние 5 строк) ---"
    tail -5 bot.log
else
    echo "ℹ️  Лог файл бота не найден"
fi

echo ""
echo "📝 Последние логи webhook сервера:"
if [ -f "webhook.log" ]; then
    echo "--- webhook.log (последние 5 строк) ---"
    tail -5 webhook.log
else
    echo "ℹ️  Лог файл webhook сервера не найден"
fi

echo ""
echo "💡 Для запуска: ./start_persistent_bot.sh"
echo "💡 Для остановки: ./stop_persistent_bot.sh"
echo "💡 Для тестирования: python3 test_webhook_simulation.py"









