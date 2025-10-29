#!/bin/bash

# Скрипт для мониторинга и автоматического перезапуска бота
# Автор: AI Assistant
# Дата: 2025-10-07

BOT_DIR="/Users/roma/1 пробник"
DAEMON_SCRIPT="$BOT_DIR/start_bot_daemon.sh"
MONITOR_LOG="$BOT_DIR/bot_monitor.log"
CHECK_INTERVAL=30  # Проверка каждые 30 секунд

# Функция для логирования
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$MONITOR_LOG"
}

# Функция для проверки, запущен ли бот
is_bot_running() {
    if [ -f "$BOT_DIR/bot_daemon.pid" ]; then
        local pid=$(cat "$BOT_DIR/bot_daemon.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Бот запущен
        else
            rm -f "$BOT_DIR/bot_daemon.pid"  # Удаляем устаревший PID файл
            return 1  # Бот не запущен
        fi
    fi
    return 1  # PID файл не существует
}

# Функция для запуска мониторинга
start_monitoring() {
    log_message "🔍 Запуск мониторинга бота (интервал: ${CHECK_INTERVAL}с)"
    
    # Запускаем бота, если он не запущен
    if ! is_bot_running; then
        log_message "🚀 Бот не запущен, запускаем..."
        "$DAEMON_SCRIPT" start
    fi
    
    # Основной цикл мониторинга
    while true; do
        if ! is_bot_running; then
            log_message "⚠️ Бот остановлен, перезапускаем..."
            "$DAEMON_SCRIPT" restart
            sleep 10  # Ждем 10 секунд после перезапуска
        else
            # Проверяем, не завис ли бот (нет активности в логах более 5 минут)
            if [ -f "$BOT_DIR/bot_daemon.log" ]; then
                local last_activity=$(tail -1 "$BOT_DIR/bot_daemon.log" | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}' || echo "")
                if [ -n "$last_activity" ]; then
                    local last_timestamp=$(date -d "$last_activity" +%s 2>/dev/null || echo "0")
                    local current_timestamp=$(date +%s)
                    local time_diff=$((current_timestamp - last_timestamp))
                    
                    # Если нет активности более 5 минут (300 секунд), перезапускаем
                    if [ $time_diff -gt 300 ]; then
                        log_message "⚠️ Бот неактивен более 5 минут, перезапускаем..."
                        "$DAEMON_SCRIPT" restart
                        sleep 10
                    fi
                fi
            fi
        fi
        
        sleep "$CHECK_INTERVAL"
    done
}

# Функция для остановки мониторинга
stop_monitoring() {
    log_message "🛑 Остановка мониторинга..."
    pkill -f "bot_monitor.sh"
}

# Основная логика
case "$1" in
    start)
        # Запускаем мониторинг в фоновом режиме
        nohup "$0" monitor > /dev/null 2>&1 &
        echo $! > "$BOT_DIR/monitor.pid"
        log_message "✅ Мониторинг запущен в фоновом режиме"
        ;;
    stop)
        stop_monitoring
        ;;
    monitor)
        start_monitoring
        ;;
    status)
        if [ -f "$BOT_DIR/monitor.pid" ]; then
            monitor_pid=$(cat "$BOT_DIR/monitor.pid")
            if ps -p "$monitor_pid" > /dev/null 2>&1; then
                echo "✅ Мониторинг запущен (PID: $monitor_pid)"
            else
                echo "❌ Мониторинг не запущен"
                rm -f "$BOT_DIR/monitor.pid"
            fi
        else
            echo "❌ Мониторинг не запущен"
        fi
        
        echo ""
        echo "Статус бота:"
        "$DAEMON_SCRIPT" status
        ;;
    *)
        echo "Использование: $0 {start|stop|monitor|status}"
        echo ""
        echo "Команды:"
        echo "  start   - Запустить мониторинг в фоновом режиме"
        echo "  stop    - Остановить мониторинг"
        echo "  monitor - Запустить мониторинг в текущем терминале"
        echo "  status  - Показать статус мониторинга и бота"
        echo ""
        echo "Файлы:"
        echo "  Лог мониторинга: $MONITOR_LOG"
        echo "  PID мониторинга: $BOT_DIR/monitor.pid"
        exit 1
        ;;
esac
