#!/bin/bash

# Установка автоматического менеджера ботов в автозагрузку

echo "🤖 УСТАНОВКА АВТОМАТИЧЕСКОГО МЕНЕДЖЕРА БОТОВ"
echo "=============================================="

# Получаем текущую директорию
CURRENT_DIR=$(pwd)
SCRIPT_PATH="$CURRENT_DIR/start_auto_manager.sh"

echo "📁 Директория проекта: $CURRENT_DIR"
echo "📄 Скрипт запуска: $SCRIPT_PATH"

# Создаем LaunchAgent для macOS
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
LAUNCH_AGENT_FILE="$LAUNCH_AGENT_DIR/com.fondklik.bot.manager.plist"

echo "🔧 Создаю LaunchAgent..."

# Создаем директорию если не существует
mkdir -p "$LAUNCH_AGENT_DIR"

# Создаем plist файл
cat > "$LAUNCH_AGENT_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fondklik.bot.manager</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_PATH</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$CURRENT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$CURRENT_DIR/bot_auto_manager.log</string>
    <key>StandardErrorPath</key>
    <string>$CURRENT_DIR/bot_auto_manager.log</string>
</dict>
</plist>
EOF

echo "✅ LaunchAgent создан: $LAUNCH_AGENT_FILE"

# Загружаем LaunchAgent
echo "🚀 Загружаю LaunchAgent..."
launchctl load "$LAUNCH_AGENT_FILE"

echo ""
echo "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo ""
echo "📋 Управление:"
echo "   Запуск:   launchctl start com.fondklik.bot.manager"
echo "   Остановка: launchctl stop com.fondklik.bot.manager"
echo "   Удаление:  launchctl unload $LAUNCH_AGENT_FILE"
echo ""
echo "📄 Логи: tail -f $CURRENT_DIR/bot_auto_manager.log"
echo ""
echo "🔄 Автоматический менеджер будет запускаться при каждой загрузке системы"








