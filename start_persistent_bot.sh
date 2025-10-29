#!/bin/bash

echo "🚀 Запуск бота для постоянной работы"
echo "===================================="

# Остановить существующие процессы
echo "🛑 Остановка существующих процессов..."
pkill -f "python3 bot_final.py" 2>/dev/null
pkill -f "python3 webhook_server_standalone.py" 2>/dev/null
sleep 2

# Очистить lock файлы
rm -f bot.lock
rm -f bot_background.pid
rm -f bot_with_webhook.pid
rm -f webhook_server.pid

# Запустить webhook сервер в фоне с nohup
echo "🔗 Запуск webhook сервера..."
nohup python3 webhook_server_standalone.py > webhook.log 2>&1 &
WEBHOOK_PID=$!
echo $WEBHOOK_PID > webhook_server.pid
echo "✅ Webhook сервер запущен (PID: $WEBHOOK_PID)"

# Подождать немного
sleep 3

# Проверить, что webhook сервер работает
echo "🏥 Проверка webhook сервера..."
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Webhook сервер работает"
else
    echo "❌ Webhook сервер не отвечает"
    exit 1
fi

# Запустить бота в фоне с nohup
echo "🤖 Запуск Telegram бота..."
nohup python3 bot_final.py > bot.log 2>&1 &
BOT_PID=$!
echo $BOT_PID > bot_persistent.pid
echo "✅ Бот запущен (PID: $BOT_PID)"

# Подождать немного
sleep 3

# Проверить, что бот работает
echo "🔍 Проверка бота..."
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo "✅ Бот работает"
else
    echo "❌ Бот не запустился. Проверьте логи:"
    tail -10 bot.log
    exit 1
fi

echo ""
echo "🎉 Система запущена для постоянной работы!"
echo "📊 Статус:"
echo "   🤖 Бот: PID $BOT_PID"
echo "   🔗 Webhook: PID $WEBHOOK_PID"
echo "   📡 Endpoint: http://localhost:8001/"
echo ""
echo "📝 Логи:"
echo "   🤖 Бот: bot.log"
echo "   🔗 Webhook: webhook.log"
echo ""
echo "💡 Для остановки: ./stop_persistent_bot.sh"
echo "💡 Для проверки статуса: ./status_persistent_bot.sh"
echo "💡 Для тестирования: python3 test_webhook_simulation.py"
echo ""
echo "✅ Бот будет работать даже после закрытия терминала!"









