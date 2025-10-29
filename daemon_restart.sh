#!/bin/bash

# Скрипт для перезапуска системного сервиса бота

echo "🔄 Перезапуск Telegram бота..."

PLIST_DEST="$HOME/Library/LaunchAgents/com.telegram.bot.plist"

# Проверяем, установлен ли сервис
if [ ! -f "$PLIST_DEST" ]; then
    echo "❌ Сервис не установлен. Сначала запустите ./install_daemon.sh"
    exit 1
fi

# Останавливаем сервис
echo "🛑 Остановка сервиса..."
launchctl unload "$PLIST_DEST" 2>/dev/null || true

# Ждем немного
sleep 2

# Запускаем сервис
echo "🚀 Запуск сервиса..."
launchctl load "$PLIST_DEST"

# Проверяем статус
echo "🔍 Проверка статуса..."
sleep 3

if launchctl list | grep -q "com.telegram.bot"; then
    echo "✅ Бот успешно перезапущен!"
    echo "📊 Статус:"
    launchctl list | grep "com.telegram.bot"
else
    echo "❌ Ошибка перезапуска"
    exit 1
fi











