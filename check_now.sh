#!/bin/bash
# Немедленная проверка ботов (не ждать 30 секунд)

# Путь к актуальной версии бота
CURRENT_DIR="/Users/roma/Desktop/Fondklik"
ACTUAL_BOT="bot_fondklik_correct.py"
ACTUAL_BOT_PATH="$CURRENT_DIR/$ACTUAL_BOT"

# Файл лога
LOG_FILE="$CURRENT_DIR/manual_check.log"

# Функция логирования
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

log "═══════════════════════════════════════════════════════"
log "🔍 НЕМЕДЛЕННАЯ ПРОВЕРКА БОТОВ [$(date '+%Y-%m-%d %H:%M:%S')]"
log "═══════════════════════════════════════════════════════"

# Подсчитываем количество ботов
BOT_PROCESSES=$(ps aux | grep -E "python.*bot.*\.py" | grep -v grep | grep -v "bot_monitor" | grep -v "check_now")
BOT_COUNT=$(echo "$BOT_PROCESSES" | grep -v "^$" | wc -l | tr -d ' ')

log "📊 Найдено запущенных ботов: $BOT_COUNT"
echo ""

# Показываем все найденные боты
if [ "$BOT_COUNT" -gt 0 ]; then
    log "📋 Список запущенных ботов:"
    echo "$BOT_PROCESSES" | while read line; do
        if [ ! -z "$line" ]; then
            PID=$(echo "$line" | awk '{print $2}')
            BOT_FILE=$(echo "$line" | awk '{print $11}')
            
            if [[ "$BOT_FILE" == *"$ACTUAL_BOT"* ]]; then
                log "  ✅ $BOT_FILE (PID: $PID) - АКТУАЛЬНАЯ ВЕРСИЯ"
            else
                log "  ⚠️  $BOT_FILE (PID: $PID) - НЕАКТУАЛЬНАЯ"
            fi
        fi
    done
    echo ""
fi

# Проверяем актуальный бот
ACTUAL_PID=$(ps aux | grep "python.*$ACTUAL_BOT" | grep -v grep | awk '{print $2}')

if [ ! -z "$ACTUAL_PID" ]; then
    log "✅ Актуальный бот работает (PID: $ACTUAL_PID)"
    ACTUAL_RUNNING=true
else
    log "⚠️  Актуальный бот НЕ запущен"
    ACTUAL_RUNNING=false
fi

# Проверяем другие боты
OTHER_PIDS=$(ps aux | grep -E "python.*bot.*\.py" | grep -v grep | grep -v "bot_monitor" | grep -v "check_now" | grep -v "$ACTUAL_BOT" | awk '{print $2}')

if [ ! -z "$OTHER_PIDS" ]; then
    OTHER_COUNT=$(echo "$OTHER_PIDS" | grep -v "^$" | wc -l | tr -d ' ')
    
    if [ "$OTHER_COUNT" -gt 0 ]; then
        log "⚠️  Найдено неактуальных ботов: $OTHER_COUNT"
        echo ""
        
        log "🗑️  Останавливаю неактуальные боты..."
        echo "$OTHER_PIDS" | while read pid; do
            if [ ! -z "$pid" ]; then
                BOT_NAME=$(ps -p $pid -o command= | awk '{print $2}')
                log "   🛑 Останавливаю: $BOT_NAME (PID: $pid)"
                
                kill $pid 2>/dev/null
                sleep 1
                
                # Если не остановился - принудительно
                if ps -p $pid > /dev/null 2>&1; then
                    log "   ⚠️  Принудительная остановка PID: $pid"
                    kill -9 $pid 2>/dev/null
                fi
                
                log "   ✅ Остановлен (PID: $pid)"
            fi
        done
        echo ""
    fi
fi

# Если актуальный бот не запущен - запускаем
if [ "$ACTUAL_RUNNING" = false ]; then
    log "🚀 Запускаю актуальный бот: $ACTUAL_BOT"
    
    cd "$CURRENT_DIR"
    
    # Проверяем .env
    if [ ! -f .env ]; then
        log "❌ Файл .env не найден!"
        exit 1
    fi
    
    # Удаляем старую блокировку если есть
    rm -f bot.lock
    
    # Запускаем бота в фоне
    nohup python3 "$ACTUAL_BOT" > bot_output.log 2>&1 &
    
    sleep 3
    
    # Проверяем что запустился
    NEW_PID=$(ps aux | grep "python.*$ACTUAL_BOT" | grep -v grep | awk '{print $2}')
    if [ ! -z "$NEW_PID" ]; then
        log "✅ Актуальный бот успешно запущен (PID: $NEW_PID)"
    else
        log "❌ Не удалось запустить актуальный бот"
        log "📝 Проверьте логи: bot_output.log"
        exit 1
    fi
fi

log "═══════════════════════════════════════════════════════"
log "✅ ПРОВЕРКА ЗАВЕРШЕНА"
log "═══════════════════════════════════════════════════════"

# Показываем финальный статус
echo ""
echo "📊 ФИНАЛЬНЫЙ СТАТУС:"
FINAL_COUNT=$(ps aux | grep -E "python.*bot.*\.py" | grep -v grep | grep -v "bot_monitor" | grep -v "check_now" | wc -l)
echo "   Всего ботов запущено: $FINAL_COUNT"

FINAL_ACTUAL=$(ps aux | grep "python.*$ACTUAL_BOT" | grep -v grep | wc -l)
if [ "$FINAL_ACTUAL" -gt 0 ]; then
    echo "   ✅ Актуальный бот: РАБОТАЕТ"
else
    echo "   ❌ Актуальный бот: НЕ РАБОТАЕТ"
fi

