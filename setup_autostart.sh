#!/bin/bash

# Скрипт для настройки автозапуска бота при загрузке системы
# Автор: AI Assistant
# Дата: 2025-10-07

BOT_DIR="/Users/roma/1 пробник"
PLIST_FILE="$HOME/Library/LaunchAgents/com.telegram.bot.plist"
DAEMON_SCRIPT="$BOT_DIR/start_bot_daemon.sh"
MONITOR_SCRIPT="$BOT_DIR/bot_monitor.sh"

# Функция для логирования
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Функция для создания plist файла
create_plist() {
    log_message "📝 Создание plist файла для автозапуска..."
    
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.telegram.bot</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$MONITOR_SCRIPT</string>
        <string>start</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$BOT_DIR</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>$BOT_DIR/launchd.log</string>
    
    <key>StandardErrorPath</key>
    <string>$BOT_DIR/launchd_error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

    log_message "✅ Plist файл создан: $PLIST_FILE"
}

# Функция для установки автозапуска
install_autostart() {
    log_message "🔧 Установка автозапуска..."
    
    # Создаем директорию LaunchAgents, если она не существует
    mkdir -p "$HOME/Library/LaunchAgents"
    
    # Создаем plist файл
    create_plist
    
    # Загружаем задачу в launchd
    launchctl load "$PLIST_FILE"
    
    if [ $? -eq 0 ]; then
        log_message "✅ Автозапуск успешно установлен"
        log_message "📋 Задача загружена в launchd"
    else
        log_message "❌ Ошибка при установке автозапуска"
        return 1
    fi
}

# Функция для удаления автозапуска
uninstall_autostart() {
    log_message "🗑️ Удаление автозапуска..."
    
    # Останавливаем задачу
    launchctl unload "$PLIST_FILE" 2>/dev/null
    
    # Удаляем plist файл
    rm -f "$PLIST_FILE"
    
    log_message "✅ Автозапуск удален"
}

# Функция для проверки статуса автозапуска
status_autostart() {
    if [ -f "$PLIST_FILE" ]; then
        log_message "✅ Автозапуск установлен"
        log_message "📁 Plist файл: $PLIST_FILE"
        
        # Проверяем, загружена ли задача
        if launchctl list | grep -q "com.telegram.bot"; then
            log_message "✅ Задача загружена в launchd"
        else
            log_message "⚠️ Задача не загружена в launchd"
        fi
    else
        log_message "❌ Автозапуск не установлен"
    fi
}

# Основная логика
case "$1" in
    install)
        install_autostart
        ;;
    uninstall)
        uninstall_autostart
        ;;
    status)
        status_autostart
        ;;
    *)
        echo "Использование: $0 {install|uninstall|status}"
        echo ""
        echo "Команды:"
        echo "  install   - Установить автозапуск бота"
        echo "  uninstall - Удалить автозапуск бота"
        echo "  status    - Показать статус автозапуска"
        echo ""
        echo "Файлы:"
        echo "  Plist файл: $PLIST_FILE"
        echo "  Демон: $DAEMON_SCRIPT"
        echo "  Монитор: $MONITOR_SCRIPT"
        exit 1
        ;;
esac






