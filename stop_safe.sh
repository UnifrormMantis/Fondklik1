#!/bin/bash

# Безопасная остановка всех ботов

echo "🛑 Безопасная остановка всех ботов..."

# Устанавливаем права на выполнение
chmod +x bot_manager.py

# Останавливаем все боты
python3 bot_manager.py stop

if [ $? -eq 0 ]; then
    echo "✅ Все боты остановлены!"
else
    echo "❌ Ошибка остановки ботов"
    exit 1
fi



