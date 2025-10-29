#!/bin/bash

# Скрипт для установки бота как системного сервиса на macOS

echo "🤖 Установка Telegram бота как системного сервиса..."

# Проверяем, что мы в правильной директории
if [ ! -f "bot_final.py" ]; then
    echo "❌ Файл bot_final.py не найден в текущей директории"
    exit 1
fi

# Останавливаем все существующие боты
echo "🛑 Остановка существующих ботов..."
python3 bot_manager.py stop 2>/dev/null || true

# Копируем plist файл в LaunchAgents
PLIST_SOURCE="com.telegram.bot.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.telegram.bot.plist"

echo "📋 Копирование конфигурации..."
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Загружаем сервис
echo "🚀 Загрузка сервиса..."
launchctl load "$PLIST_DEST"

# Проверяем статус
echo "🔍 Проверка статуса..."
sleep 3

if launchctl list | grep -q "com.telegram.bot"; then
    echo "✅ Бот успешно установлен как системный сервис!"
    echo "📊 Статус:"
    launchctl list | grep "com.telegram.bot"
    echo ""
    echo "🎉 Бот будет автоматически запускаться при загрузке системы"
    echo "📝 Логи: bot.log и bot_error.log в текущей директории"
    echo ""
    echo "💡 Команды управления:"
    echo "   ./uninstall_daemon.sh  - Удалить сервис"
    echo "   ./daemon_status.sh     - Проверить статус"
    echo "   ./daemon_restart.sh    - Перезапустить сервис"
else
    echo "❌ Ошибка установки сервиса"
    exit 1
fi











