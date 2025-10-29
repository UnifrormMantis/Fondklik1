#!/bin/bash

# Скрипт для запуска демона бота

echo "🤖 Запуск демона Telegram бота..."

# Останавливаем все существующие боты
echo "🛑 Остановка существующих ботов..."
python3 bot_manager.py stop 2>/dev/null || true

# Ждем немного
sleep 2

# Запускаем демон в фоне
echo "🚀 Запуск демона..."
nohup python3 bot_daemon.py start > daemon_output.log 2>&1 &

# Получаем PID демона
DAEMON_PID=$!

# Сохраняем PID
echo $DAEMON_PID > daemon.pid

echo "✅ Демон запущен (PID: $DAEMON_PID)"
echo "📝 Лог демона: daemon_output.log"
echo "📝 Лог бота: daemon.log"
echo "💾 PID демона: daemon.pid"

# Проверяем через несколько секунд
sleep 3

if ps -p $DAEMON_PID > /dev/null; then
    echo "🎉 Демон работает успешно!"
    echo "💡 Для остановки: ./stop_daemon.sh"
    echo "💡 Для проверки статуса: ./status_daemon.sh"
else
    echo "❌ Демон не запустился. Проверьте логи."
    exit 1
fi











