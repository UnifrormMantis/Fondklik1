#!/bin/bash

echo "🚀 Запуск бота с webhook сервером"
echo "================================="

# Остановить существующие процессы
echo "🛑 Остановка существующих процессов..."
pkill -f "python3 bot_final.py" 2>/dev/null
pkill -f "python3 webhook_server.py" 2>/dev/null
sleep 2

# Запустить webhook сервер в фоне
echo "🔗 Запуск webhook сервера..."
python3 webhook_server_standalone.py &
WEBHOOK_PID=$!
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

# Запустить бота в фоне
echo "🤖 Запуск Telegram бота..."
python3 bot_final.py &
BOT_PID=$!
echo "✅ Бот запущен (PID: $BOT_PID)"

# Сохранить PID в файл
echo $BOT_PID > bot_with_webhook.pid
echo $WEBHOOK_PID > webhook_server.pid

echo ""
echo "🎉 Система запущена успешно!"
echo "📊 Статус:"
echo "   🤖 Бот: PID $BOT_PID"
echo "   🔗 Webhook: PID $WEBHOOK_PID"
echo "   📡 Endpoint: http://localhost:8001/"
echo ""
echo "💡 Для остановки: ./stop_bot_with_webhook.sh"
echo "💡 Для проверки статуса: ./status_bot_with_webhook.sh"
echo "💡 Для тестирования: python3 test_webhook_simulation.py"
