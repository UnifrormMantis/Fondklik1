#!/bin/bash

# Безопасный запуск бота с контролем количества

echo "🤖 Безопасный запуск бота..."

# Устанавливаем права на выполнение
chmod +x bot_manager.py

# Запускаем менеджер
python3 bot_manager.py start

if [ $? -eq 0 ]; then
    echo "✅ Бот запущен успешно!"
    echo "📊 Для проверки статуса: python3 bot_manager.py status"
    echo "🛑 Для остановки: python3 bot_manager.py stop"
else
    echo "❌ Ошибка запуска бота"
    exit 1
fi

















