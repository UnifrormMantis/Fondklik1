#!/bin/bash

# Скрипт для проверки статуса демона бота

echo "📊 Статус демона Telegram бота..."

# Проверяем PID демона
if [ -f "daemon.pid" ]; then
    DAEMON_PID=$(cat daemon.pid)
    echo "💾 PID демона: $DAEMON_PID"
    
    if ps -p $DAEMON_PID > /dev/null; then
        echo "✅ Демон работает (PID: $DAEMON_PID)"
        
        # Показываем информацию о демоне
        echo "📊 Информация о демоне:"
        ps -p $DAEMON_PID -o pid,ppid,etime,pcpu,pmem,command
    else
        echo "❌ Демон не работает (процесс не найден)"
        echo "🗑️  Удаляю устаревший PID файл..."
        rm -f daemon.pid
    fi
else
    echo "ℹ️  PID файл демона не найден"
fi

echo ""

# Проверяем статус через демон
echo "🔍 Статус бота через демон:"
python3 bot_daemon.py status 2>/dev/null || echo "❌ Демон не отвечает"

echo ""

# Проверяем все процессы бота
echo "🔍 Все процессы бота:"
python3 bot_manager.py status

echo ""

# Показываем последние логи демона
echo "📝 Последние логи демона:"
if [ -f "daemon.log" ]; then
    echo "--- daemon.log (последние 10 строк) ---"
    tail -10 daemon.log
else
    echo "ℹ️  Файл daemon.log не найден"
fi

if [ -f "daemon_output.log" ]; then
    echo "--- daemon_output.log (последние 5 строк) ---"
    tail -5 daemon_output.log
else
    echo "ℹ️  Файл daemon_output.log не найден"
fi











