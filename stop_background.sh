#!/bin/bash

# Скрипт для остановки фонового бота

echo "🛑 Остановка фонового Telegram бота..."

# Читаем PID из файла
if [ -f "bot_background.pid" ]; then
    BOT_PID=$(cat bot_background.pid)
    echo "🔄 Найден PID: $BOT_PID"
    
    # Проверяем, работает ли процесс
    if ps -p $BOT_PID > /dev/null; then
        echo "🛑 Остановка процесса..."
        kill -TERM $BOT_PID
        
        # Ждем завершения
        sleep 3
        
        # Проверяем, остановился ли
        if ps -p $BOT_PID > /dev/null; then
            echo "🔄 Принудительная остановка..."
            kill -9 $BOT_PID
        fi
        
        echo "✅ Процесс остановлен"
    else
        echo "ℹ️  Процесс уже не работает"
    fi
    
    # Удаляем файл PID
    rm -f bot_background.pid
else
    echo "ℹ️  Файл PID не найден"
fi

# Дополнительно останавливаем все боты через менеджер
echo "🛑 Дополнительная очистка..."
python3 bot_manager.py stop 2>/dev/null || true

echo "🎉 Фоновый бот остановлен"











