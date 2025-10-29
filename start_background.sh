#!/bin/bash

# Скрипт для запуска бота в фоновом режиме с nohup

echo "🤖 Запуск Telegram бота в фоновом режиме..."

# Останавливаем все существующие боты
echo "🛑 Остановка существующих ботов..."
python3 bot_manager.py stop 2>/dev/null || true

# Ждем немного
sleep 2

# Создаем директорию для логов если не существует
mkdir -p logs

# Запускаем бота в фоне с nohup
echo "🚀 Запуск бота в фоне..."
nohup python3 bot_final.py > logs/bot_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# Получаем PID
BOT_PID=$!

# Сохраняем PID в файл
echo $BOT_PID > bot_background.pid

echo "✅ Бот запущен в фоновом режиме (PID: $BOT_PID)"
echo "📝 Лог: logs/bot_$(date +%Y%m%d_%H%M%S).log"
echo "💾 PID сохранен в: bot_background.pid"

# Проверяем через несколько секунд
sleep 3

if ps -p $BOT_PID > /dev/null; then
    echo "🎉 Бот работает успешно!"
    echo "💡 Для остановки: ./stop_background.sh"
    echo "💡 Для проверки статуса: ./status_background.sh"
else
    echo "❌ Бот не запустился. Проверьте логи."
    exit 1
fi











