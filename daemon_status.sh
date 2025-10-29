#!/bin/bash

# Скрипт для проверки статуса системного сервиса бота

echo "📊 Статус Telegram бота..."

# Проверяем LaunchAgent
echo "🔍 Проверка системного сервиса:"
if launchctl list | grep -q "com.telegram.bot"; then
    echo "✅ Сервис загружен в систему"
    launchctl list | grep "com.telegram.bot"
else
    echo "❌ Сервис не загружен"
fi

echo ""

# Проверяем процессы
echo "🔍 Проверка запущенных процессов:"
python3 bot_manager.py status

echo ""

# Проверяем логи
echo "📝 Последние записи в логах:"
if [ -f "bot.log" ]; then
    echo "--- bot.log (последние 5 строк) ---"
    tail -5 bot.log
else
    echo "❌ Файл bot.log не найден"
fi

if [ -f "bot_error.log" ]; then
    echo "--- bot_error.log (последние 5 строк) ---"
    tail -5 bot_error.log
else
    echo "ℹ️  Файл bot_error.log не найден (ошибок нет)"
fi











