#!/bin/bash

# Скрипт для проверки статуса фонового бота

echo "📊 Статус фонового Telegram бота..."

# Проверяем PID файл
if [ -f "bot_background.pid" ]; then
    BOT_PID=$(cat bot_background.pid)
    echo "💾 PID из файла: $BOT_PID"
    
    if ps -p $BOT_PID > /dev/null; then
        echo "✅ Бот работает (PID: $BOT_PID)"
        
        # Показываем информацию о процессе
        echo "📊 Информация о процессе:"
        ps -p $BOT_PID -o pid,ppid,etime,pcpu,pmem,command
    else
        echo "❌ Бот не работает (процесс не найден)"
        echo "🗑️  Удаляю устаревший PID файл..."
        rm -f bot_background.pid
    fi
else
    echo "ℹ️  PID файл не найден"
fi

echo ""

# Проверяем все процессы бота
echo "🔍 Все процессы бота:"
python3 bot_manager.py status

echo ""

# Показываем последние логи
echo "📝 Последние логи:"
if [ -d "logs" ]; then
    LATEST_LOG=$(ls -t logs/bot_*.log 2>/dev/null | head -1)
    if [ ! -z "$LATEST_LOG" ]; then
        echo "--- $LATEST_LOG (последние 10 строк) ---"
        tail -10 "$LATEST_LOG"
    else
        echo "ℹ️  Логи не найдены"
    fi
else
    echo "ℹ️  Директория logs не найдена"
fi











