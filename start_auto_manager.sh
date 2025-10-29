#!/bin/bash

# Автоматический запуск менеджера ботов
echo "🤖 ЗАПУСК АВТОМАТИЧЕСКОГО МЕНЕДЖЕРА БОТОВ"

# Останавливаем все боты
echo "🛑 Останавливаю все боты..."
python3 bot_auto_manager.py stop

# Ждем 2 секунды
sleep 2

# Запускаем менеджер в режиме мониторинга
echo "🚀 Запускаю автоматический менеджер..."
nohup python3 bot_auto_manager.py monitor > bot_auto_manager.log 2>&1 &

echo "✅ Автоматический менеджер запущен в фоне"
echo "📋 Логи: tail -f bot_auto_manager.log"
echo "🛑 Остановка: pkill -f bot_auto_manager.py"








