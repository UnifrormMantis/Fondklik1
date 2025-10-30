#!/bin/bash
# Запуск системы мониторинга ботов

MONITOR_SCRIPT="/Users/roma/Desktop/Fondklik/bot_monitor.sh"
PID_FILE="/Users/roma/Desktop/Fondklik/monitor.pid"

# Проверяем не запущен ли уже монитор
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠️  Монитор уже запущен (PID: $OLD_PID)"
        exit 1
    else
        echo "🗑️  Удаляем старый PID файл"
        rm -f "$PID_FILE"
    fi
fi

echo "🚀 Запуск системы мониторинга ботов..."

# Запускаем монитор в фоне
nohup "$MONITOR_SCRIPT" > /dev/null 2>&1 &

MONITOR_PID=$!
echo $MONITOR_PID > "$PID_FILE"

sleep 2

# Проверяем что запустился
if ps -p $MONITOR_PID > /dev/null 2>&1; then
    echo "✅ Система мониторинга запущена (PID: $MONITOR_PID)"
    echo "📝 Логи: /Users/roma/Desktop/Fondklik/monitor.log"
    echo ""
    echo "Для остановки используйте: ./stop_monitor.sh"
else
    echo "❌ Не удалось запустить систему мониторинга"
    rm -f "$PID_FILE"
    exit 1
fi

