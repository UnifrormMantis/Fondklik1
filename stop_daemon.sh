#!/bin/bash

# Скрипт для остановки демона бота

echo "🛑 Остановка демона Telegram бота..."

# Читаем PID демона
if [ -f "daemon.pid" ]; then
    DAEMON_PID=$(cat daemon.pid)
    echo "🔄 Найден PID демона: $DAEMON_PID"
    
    # Проверяем, работает ли демон
    if ps -p $DAEMON_PID > /dev/null; then
        echo "🛑 Остановка демона..."
        kill -TERM $DAEMON_PID
        
        # Ждем завершения
        sleep 3
        
        # Проверяем, остановился ли
        if ps -p $DAEMON_PID > /dev/null; then
            echo "🔄 Принудительная остановка демона..."
            kill -9 $DAEMON_PID
        fi
        
        echo "✅ Демон остановлен"
    else
        echo "ℹ️  Демон уже не работает"
    fi
    
    # Удаляем файл PID
    rm -f daemon.pid
else
    echo "ℹ️  Файл PID демона не найден"
fi

# Дополнительно останавливаем все боты
echo "🛑 Дополнительная очистка..."
python3 bot_manager.py stop 2>/dev/null || true

echo "🎉 Демон и все боты остановлены"











