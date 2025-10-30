#!/bin/bash
# Умный мониторинг ботов FondKlik
# Проверяет каждые 30 секунд и управляет версиями

# Путь к актуальной версии бота
CURRENT_DIR="/Users/roma/Desktop/Fondklik"
ACTUAL_BOT="bot_fondklik_correct.py"
ACTUAL_BOT_PATH="$CURRENT_DIR/$ACTUAL_BOT"

# Файл лога
LOG_FILE="$CURRENT_DIR/monitor.log"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Функция проверки запущенных ботов
check_bots() {
    # Находим все Python процессы с "bot" в названии
    BOT_PROCESSES=$(ps aux | grep -E "python.*bot.*\.py" | grep -v grep | grep -v "bot_monitor")
    
    if [ -z "$BOT_PROCESSES" ]; then
        echo "0"
        return
    fi
    
    echo "$BOT_PROCESSES" | wc -l
}

# Функция получения PID актуального бота
get_actual_bot_pid() {
    ps aux | grep "python.*$ACTUAL_BOT" | grep -v grep | awk '{print $2}'
}

# Функция получения всех PIDs неактуальных ботов
get_other_bots_pids() {
    ps aux | grep -E "python.*bot.*\.py" | grep -v grep | grep -v "bot_monitor" | grep -v "$ACTUAL_BOT" | awk '{print $2}'
}

# Функция запуска актуального бота - ОТКЛЮЧЕНА
# Монитор больше НЕ запускает ботов автоматически
start_actual_bot() {
    log "⚠️  Автозапуск бота отключен"
    log "💡 Используйте ./start_all.sh для запуска"
    return 1
}

# Функция остановки бота по PID
stop_bot() {
    local PID=$1
    local BOT_NAME=$(ps -p $PID -o command= | awk '{print $2}')
    
    log "🛑 Остановка неактуального бота: $BOT_NAME (PID: $PID)"
    
    kill $PID 2>/dev/null
    sleep 2
    
    # Если не остановился - принудительно
    if ps -p $PID > /dev/null 2>&1; then
        log "⚠️  Принудительная остановка PID: $PID"
        kill -9 $PID 2>/dev/null
    fi
    
    log "✅ Бот остановлен (PID: $PID)"
}

# Основная функция мониторинга
monitor() {
    log "═══════════════════════════════════════════════════════"
    log "🔍 ДИАГНОСТИКА БОТОВ"
    
    # Подсчитываем ВСЕ запущенные боты
    BOT_COUNT=$(check_bots)
    log "📊 Найдено запущенных ботов: $BOT_COUNT"
    
    # КРИТИЧЕСКАЯ ПРОВЕРКА: Если ботов больше 1 - ОСТАНАВЛИВАЕМ ВСЕ
    if [ "$BOT_COUNT" -gt 1 ]; then
        log "🚨 КРИТИЧНО! Обнаружено $BOT_COUNT ботов (должен быть только 1)"
        log "📋 Список всех ботов:"
        
        # Показываем все боты
        ps aux | grep -E "python.*bot.*\.py" | grep -v grep | grep -v "bot_monitor" | while read line; do
            BOT_FILE=$(echo "$line" | awk '{print $11}')
            BOT_PID=$(echo "$line" | awk '{print $2}')
            log "   └─ $BOT_FILE (PID: $BOT_PID)"
        done
        
        log "🛑 ОСТАНАВЛИВАЮ ВСЕ БОТЫ..."
        pkill -9 -f "python.*bot.*\.py" 2>/dev/null
        rm -f "$CURRENT_DIR/bot.lock"
        
        log "✅ Все боты остановлены (множественный запуск)"
        log "⚠️  Требуется ручной запуск через ./start_all.sh"
        
    elif [ "$BOT_COUNT" -eq 1 ]; then
        # Показываем какой бот работает
        BOT_INFO=$(ps aux | grep -E "python.*bot.*\.py" | grep -v grep | grep -v "bot_monitor")
        BOT_FILE=$(echo "$BOT_INFO" | awk '{print $11}')
        BOT_PID=$(echo "$BOT_INFO" | awk '{print $2}')
        
        log "✅ Работает 1 бот: $BOT_FILE (PID: $BOT_PID)"
        
        # Проверяем что это актуальная версия
        if echo "$BOT_FILE" | grep -q "$ACTUAL_BOT"; then
            log "✅ Версия АКТУАЛЬНАЯ"
        else
            log "⚠️  ВНИМАНИЕ: Работает НЕ актуальная версия!"
            log "   Актуальная: $ACTUAL_BOT"
            log "   Работает:   $BOT_FILE"
        fi
        
    else
        log "ℹ️  Боты не запущены"
        log "💡 Запустите: ./start_all.sh"
    fi
    
    # Диагностика логов (только информация, БЕЗ остановки)
    if [ -f "$CURRENT_DIR/bot_output.log" ]; then
        if tail -20 "$CURRENT_DIR/bot_output.log" | grep -q "Conflict"; then
            log "⚠️  ДИАГНОСТИКА: В логах обнаружен Conflict"
            log "💡 Возможно бот запущен на другом сервере (Railway)"
        fi
    fi
    
    log "═══════════════════════════════════════════════════════"
    echo ""
}

# Главный цикл
log "🤖 СИСТЕМА МОНИТОРИНГА БОТОВ ЗАПУЩЕНА"
log "📍 Актуальная версия: $ACTUAL_BOT"
log "📂 Рабочая директория: $CURRENT_DIR"
log "⏱️  Интервал проверки: 30 секунд"
log "═══════════════════════════════════════════════════════"

# Первая проверка сразу
monitor

# Далее проверяем каждые 30 секунд
while true; do
    sleep 30
    monitor
done

