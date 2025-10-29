#!/bin/bash

# Скрипт для запуска бота в фоновом режиме
# Автор: AI Assistant
# Дата: 2025-10-07

BOT_DIR="/Users/roma/1 пробник"
BOT_FILE="bot_fondklik_correct.py"
PID_FILE="$BOT_DIR/bot_daemon.pid"
LOG_FILE="$BOT_DIR/bot_daemon.log"
LOCK_FILE="$BOT_DIR/bot.lock"

# Функция для логирования
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Функция для проверки, запущен ли бот
is_bot_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Бот запущен
        else
            rm -f "$PID_FILE"  # Удаляем устаревший PID файл
            return 1  # Бот не запущен
        fi
    fi
    return 1  # PID файл не существует
}

# Функция для остановки бота
stop_bot() {
    log_message "🛑 Остановка бота..."
    
    # Удаляем lock файл
    rm -f "$LOCK_FILE"
    
    if is_bot_running; then
        local pid=$(cat "$PID_FILE")
        log_message "📋 Найден процесс бота с PID: $pid"
        
        # Пытаемся корректно остановить процесс
        kill -TERM "$pid" 2>/dev/null
        
        # Ждем до 10 секунд для корректного завершения
        for i in {1..10}; do
            if ! ps -p "$pid" > /dev/null 2>&1; then
                log_message "✅ Бот корректно остановлен"
                rm -f "$PID_FILE"
                return 0
            fi
            sleep 1
        done
        
        # Если процесс не остановился, принудительно завершаем
        log_message "⚠️ Принудительное завершение процесса..."
        kill -KILL "$pid" 2>/dev/null
        sleep 2
        
        if ! ps -p "$pid" > /dev/null 2>&1; then
            log_message "✅ Бот принудительно остановлен"
            rm -f "$PID_FILE"
        else
            log_message "❌ Не удалось остановить бота"
            return 1
        fi
    else
        log_message "ℹ️ Бот не запущен"
    fi
}

# Функция для запуска бота
start_bot() {
    log_message "🚀 Запуск бота в фоновом режиме..."
    
    # Проверяем, не запущен ли уже бот
    if is_bot_running; then
        log_message "⚠️ Бот уже запущен!"
        return 1
    fi
    
    # Переходим в директорию бота
    cd "$BOT_DIR" || {
        log_message "❌ Не удалось перейти в директорию: $BOT_DIR"
        return 1
    }
    
    # Удаляем старые lock файлы
    rm -f "$LOCK_FILE"
    
    # Запускаем бота в фоновом режиме
    nohup python3 "$BOT_FILE" > "$LOG_FILE" 2>&1 &
    local bot_pid=$!
    
    # Сохраняем PID
    echo "$bot_pid" > "$PID_FILE"
    
    # Ждем немного и проверяем, что бот запустился
    sleep 3
    
    if ps -p "$bot_pid" > /dev/null 2>&1; then
        log_message "✅ Бот успешно запущен с PID: $bot_pid"
        log_message "📁 Логи: $LOG_FILE"
        log_message "📋 PID файл: $PID_FILE"
        return 0
    else
        log_message "❌ Не удалось запустить бота"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Функция для перезапуска бота
restart_bot() {
    log_message "🔄 Перезапуск бота..."
    stop_bot
    sleep 2
    start_bot
}

# Функция для проверки статуса
status_bot() {
    if is_bot_running; then
        local pid=$(cat "$PID_FILE")
        log_message "✅ Бот запущен (PID: $pid)"
        
        # Показываем информацию о процессе
        ps -p "$pid" -o pid,ppid,etime,pcpu,pmem,command 2>/dev/null || true
        
        # Показываем последние строки лога
        if [ -f "$LOG_FILE" ]; then
            log_message "📋 Последние строки лога:"
            tail -5 "$LOG_FILE" | while read line; do
                echo "   $line"
            done
        fi
    else
        log_message "❌ Бот не запущен"
    fi
}

# Основная логика
case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        status_bot
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status}"
        echo ""
        echo "Команды:"
        echo "  start   - Запустить бота в фоновом режиме"
        echo "  stop    - Остановить бота"
        echo "  restart - Перезапустить бота"
        echo "  status  - Показать статус бота"
        echo ""
        echo "Файлы:"
        echo "  PID файл: $PID_FILE"
        echo "  Лог файл: $LOG_FILE"
        echo "  Lock файл: $LOCK_FILE"
        exit 1
        ;;
esac






