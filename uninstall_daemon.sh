#!/bin/bash

# Скрипт для удаления бота как системного сервиса

echo "🛑 Удаление Telegram бота из системных сервисов..."

PLIST_DEST="$HOME/Library/LaunchAgents/com.telegram.bot.plist"

# Останавливаем и выгружаем сервис
if [ -f "$PLIST_DEST" ]; then
    echo "🔄 Остановка сервиса..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    
    echo "🗑️  Удаление конфигурации..."
    rm -f "$PLIST_DEST"
    
    echo "✅ Сервис удален"
else
    echo "ℹ️  Сервис не найден"
fi

# Останавливаем все боты
echo "🛑 Остановка всех ботов..."
python3 bot_manager.py stop 2>/dev/null || true

echo "🎉 Бот полностью удален из системных сервисов"











