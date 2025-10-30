#!/bin/bash
# Проверка статуса всей системы: БОТ + МОНИТОР

CURRENT_DIR="/Users/roma/Desktop/Fondklik"
ACTUAL_BOT="bot_fondklik_correct.py"

echo "═══════════════════════════════════════════════════════"
echo "        📊 СТАТУС СИСТЕМЫ FONDKLIK BOT"
echo "═══════════════════════════════════════════════════════"
echo ""

# 1. Проверяем актуальный бот
echo "🤖 БОТ:"
ACTUAL_PID=$(ps aux | grep "python.*$ACTUAL_BOT" | grep -v grep | awk '{print $2}')
if [ ! -z "$ACTUAL_PID" ]; then
    RUNTIME=$(ps -p $ACTUAL_PID -o etime= | tr -d ' ')
    echo "   ✅ РАБОТАЕТ"
    echo "   PID: $ACTUAL_PID"
    echo "   Время работы: $RUNTIME"
else
    echo "   ❌ НЕ ЗАПУЩЕН"
fi
echo ""

# 2. Проверяем монитор
echo "👁️  МОНИТОР:"
if [ -f "$CURRENT_DIR/monitor.pid" ]; then
    MONITOR_PID=$(cat "$CURRENT_DIR/monitor.pid")
    if ps -p $MONITOR_PID > /dev/null 2>&1; then
        RUNTIME=$(ps -p $MONITOR_PID -o etime= | tr -d ' ')
        echo "   ✅ РАБОТАЕТ"
        echo "   PID: $MONITOR_PID"
        echo "   Время работы: $RUNTIME"
    else
        echo "   ❌ НЕ ЗАПУЩЕН (PID файл есть, но процесс не найден)"
    fi
else
    echo "   ❌ НЕ ЗАПУЩЕН"
fi
echo ""

# 3. Проверяем все запущенные боты
echo "📋 ВСЕ ЗАПУЩЕННЫЕ БОТЫ:"
BOT_PROCESSES=$(ps aux | grep "python.*bot.*\.py" | grep -v grep | grep -v monitor)
if [ -z "$BOT_PROCESSES" ]; then
    echo "   Нет запущенных ботов"
else
    echo "$BOT_PROCESSES" | while read line; do
        PID=$(echo "$line" | awk '{print $2}')
        BOT=$(echo "$line" | awk '{print $11}')
        RUNTIME=$(ps -p $PID -o etime= | tr -d ' ')
        
        if [[ "$BOT" == *"$ACTUAL_BOT"* ]]; then
            echo "   ✅ $BOT (PID: $PID, $RUNTIME) - АКТУАЛЬНАЯ"
        else
            echo "   ⚠️  $BOT (PID: $PID, $RUNTIME) - неактуальная"
        fi
    done
fi
echo ""

# 4. Последние логи
echo "═══════════════════════════════════════════════════════"
echo "📝 ПОСЛЕДНИЕ ЛОГИ:"
echo ""

if [ -f "$CURRENT_DIR/bot_output.log" ]; then
    echo "Бот (последние 5 строк):"
    tail -5 "$CURRENT_DIR/bot_output.log" | sed 's/^/   /'
    echo ""
fi

if [ -f "$CURRENT_DIR/monitor.log" ]; then
    echo "Монитор (последние 5 строк):"
    tail -5 "$CURRENT_DIR/monitor.log" | sed 's/^/   /'
    echo ""
fi

echo "═══════════════════════════════════════════════════════"

