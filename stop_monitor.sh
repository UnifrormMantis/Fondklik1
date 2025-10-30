#!/bin/bash
# Остановка системы мониторинга ботов

PID_FILE="/Users/roma/Desktop/Fondklik/monitor.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "❌ Монитор не запущен (PID файл не найден)"
    exit 1
fi

MONITOR_PID=$(cat "$PID_FILE")

if ! ps -p $MONITOR_PID > /dev/null 2>&1; then
    echo "⚠️  Процесс монитора не найден (PID: $MONITOR_PID)"
    rm -f "$PID_FILE"
    exit 1
fi

echo "🛑 Остановка системы мониторинга (PID: $MONITOR_PID)..."

kill $MONITOR_PID
sleep 2

# Проверяем что остановился
if ps -p $MONITOR_PID > /dev/null 2>&1; then
    echo "⚠️  Принудительная остановка..."
    kill -9 $MONITOR_PID
fi

rm -f "$PID_FILE"

echo "✅ Система мониторинга остановлена"

