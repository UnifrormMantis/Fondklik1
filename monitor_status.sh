#!/bin/bash
# Проверка статуса системы мониторинга

PID_FILE="/Users/roma/Desktop/Fondklik/monitor.pid"
LOG_FILE="/Users/roma/Desktop/Fondklik/monitor.log"

echo "═══════════════════════════════════════════════════════"
echo "        СТАТУС СИСТЕМЫ МОНИТОРИНГА БОТОВ"
echo "═══════════════════════════════════════════════════════"
echo ""

# Проверяем PID файл
if [ -f "$PID_FILE" ]; then
    MONITOR_PID=$(cat "$PID_FILE")
    
    if ps -p $MONITOR_PID > /dev/null 2>&1; then
        echo "✅ Монитор РАБОТАЕТ (PID: $MONITOR_PID)"
        
        # Показываем информацию о процессе
        echo ""
        echo "📊 Информация о процессе:"
        ps -p $MONITOR_PID -o pid,etime,command | tail -1
    else
        echo "❌ Монитор НЕ РАБОТАЕТ (процесс не найден)"
        echo "   PID файл существует, но процесс завершен"
    fi
else
    echo "❌ Монитор НЕ ЗАПУЩЕН (PID файл не найден)"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "                  ЗАПУЩЕННЫЕ БОТЫ"
echo "═══════════════════════════════════════════════════════"
echo ""

BOT_COUNT=$(ps aux | grep -E "python.*bot.*\.py" | grep -v grep | grep -v "bot_monitor" | wc -l)

if [ "$BOT_COUNT" -eq 0 ]; then
    echo "⚠️  Ботов не запущено"
else
    echo "📊 Найдено ботов: $BOT_COUNT"
    echo ""
    ps aux | grep -E "python.*bot.*\.py" | grep -v grep | grep -v "bot_monitor" | while read line; do
        PID=$(echo "$line" | awk '{print $2}')
        BOT=$(echo "$line" | awk '{print $11}')
        RUNTIME=$(ps -p $PID -o etime= | tr -d ' ')
        
        if [[ "$BOT" == *"bot_fondklik_correct.py"* ]]; then
            echo "  ✅ $BOT (PID: $PID, работает: $RUNTIME) - АКТУАЛЬНАЯ ВЕРСИЯ"
        else
            echo "  ⚠️  $BOT (PID: $PID, работает: $RUNTIME) - неактуальная"
        fi
    done
fi

echo ""
echo "═══════════════════════════════════════════════════════"

# Показываем последние строки лога если есть
if [ -f "$LOG_FILE" ]; then
    echo ""
    echo "📝 Последние 10 строк лога:"
    echo ""
    tail -10 "$LOG_FILE"
fi

