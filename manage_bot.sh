#!/bin/bash

# Главный скрипт для управления ботом
# Автор: AI Assistant
# Дата: 2025-10-07

BOT_DIR="/Users/roma/1 пробник"
DAEMON_SCRIPT="$BOT_DIR/start_bot_daemon.sh"
MONITOR_SCRIPT="$BOT_DIR/bot_monitor.sh"
AUTOSTART_SCRIPT="$BOT_DIR/setup_autostart.sh"

# Функция для логирования
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Функция для показа справки
show_help() {
    echo "🤖 УПРАВЛЕНИЕ ТЕЛЕГРАМ БОТОМ"
    echo "================================"
    echo ""
    echo "📋 ОСНОВНЫЕ КОМАНДЫ:"
    echo "  start     - Запустить бота"
    echo "  stop      - Остановить бота"
    echo "  restart   - Перезапустить бота"
    echo "  status    - Показать статус бота"
    echo ""
    echo "🔍 МОНИТОРИНГ:"
    echo "  monitor   - Запустить мониторинг (автоперезапуск)"
    echo "  unmonitor - Остановить мониторинг"
    echo ""
    echo "🚀 АВТОЗАПУСК:"
    echo "  autostart - Установить автозапуск при загрузке"
    echo "  noautostart - Удалить автозапуск"
    echo ""
    echo "📊 ИНФОРМАЦИЯ:"
    echo "  logs      - Показать логи бота"
    echo "  monitor-logs - Показать логи мониторинга"
    echo "  info      - Показать информацию о системе"
    echo ""
    echo "🛠️ ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:"
    echo "  $0 start          # Запустить бота"
    echo "  $0 monitor        # Запустить с автоперезапуском"
    echo "  $0 autostart      # Установить автозапуск"
    echo "  $0 status         # Проверить статус"
    echo ""
}

# Функция для показа логов
show_logs() {
    local log_file="$BOT_DIR/bot_daemon.log"
    if [ -f "$log_file" ]; then
        echo "📋 ЛОГИ БОТА (последние 20 строк):"
        echo "=================================="
        tail -20 "$log_file"
    else
        echo "❌ Лог файл не найден: $log_file"
    fi
}

# Функция для показа логов мониторинга
show_monitor_logs() {
    local log_file="$BOT_DIR/bot_monitor.log"
    if [ -f "$log_file" ]; then
        echo "🔍 ЛОГИ МОНИТОРИНГА (последние 20 строк):"
        echo "========================================="
        tail -20 "$log_file"
    else
        echo "❌ Лог файл мониторинга не найден: $log_file"
    fi
}

# Функция для показа информации о системе
show_info() {
    echo "📊 ИНФОРМАЦИЯ О СИСТЕМЕ"
    echo "======================="
    echo ""
    echo "📁 Директория бота: $BOT_DIR"
    echo "🐍 Python версия: $(python3 --version 2>/dev/null || echo 'Не установлен')"
    echo "💾 Свободное место: $(df -h "$BOT_DIR" | tail -1 | awk '{print $4}')"
    echo "🕐 Время системы: $(date)"
    echo ""
    echo "📋 ФАЙЛЫ БОТА:"
    echo "  Основной файл: bot_fondklik_correct.py"
    echo "  База данных: bot_database.db"
    echo "  PID файл: bot_daemon.pid"
    echo "  Лог бота: bot_daemon.log"
    echo "  Лог мониторинга: bot_monitor.log"
    echo ""
    echo "🔧 СКРИПТЫ:"
    echo "  Демон: start_bot_daemon.sh"
    echo "  Мониторинг: bot_monitor.sh"
    echo "  Автозапуск: setup_autostart.sh"
    echo "  Управление: manage_bot.sh"
}

# Основная логика
case "$1" in
    start)
        log_message "🚀 Запуск бота..."
        "$DAEMON_SCRIPT" start
        ;;
    stop)
        log_message "🛑 Остановка бота..."
        "$DAEMON_SCRIPT" stop
        ;;
    restart)
        log_message "🔄 Перезапуск бота..."
        "$DAEMON_SCRIPT" restart
        ;;
    status)
        log_message "📊 Статус бота:"
        "$DAEMON_SCRIPT" status
        echo ""
        log_message "🔍 Статус мониторинга:"
        "$MONITOR_SCRIPT" status
        ;;
    monitor)
        log_message "🔍 Запуск мониторинга..."
        "$MONITOR_SCRIPT" start
        ;;
    unmonitor)
        log_message "🛑 Остановка мониторинга..."
        "$MONITOR_SCRIPT" stop
        ;;
    autostart)
        log_message "🚀 Установка автозапуска..."
        "$AUTOSTART_SCRIPT" install
        ;;
    noautostart)
        log_message "🗑️ Удаление автозапуска..."
        "$AUTOSTART_SCRIPT" uninstall
        ;;
    logs)
        show_logs
        ;;
    monitor-logs)
        show_monitor_logs
        ;;
    info)
        show_info
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Неизвестная команда: $1"
        echo ""
        show_help
        exit 1
        ;;
esac