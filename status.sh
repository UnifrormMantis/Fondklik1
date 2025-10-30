#!/bin/bash
# Проверка статуса FondKlik Bot

echo "📊 Проверка статуса FondKlik Bot..."
echo ""

# Проверяем процесс бота
BOT_PID=$(ps aux | grep "python3 bot_fondklik_correct.py" | grep -v grep | awk '{print $2}')

if [ ! -z "$BOT_PID" ]; then
    echo "✅ Бот ЗАПУЩЕН (PID: $BOT_PID)"
    
    # Показываем информацию о процессе
    echo ""
    echo "Детали процесса:"
    ps aux | grep $BOT_PID | grep -v grep
    
    # Проверяем блокировку
    if [ -f "bot.lock" ]; then
        echo ""
        echo "🔒 Файл блокировки: АКТИВЕН"
    else
        echo ""
        echo "⚠️  Файл блокировки: НЕ НАЙДЕН"
    fi
    
    # Показываем последние логи
    if [ -f "bot.log" ]; then
        echo ""
        echo "📝 Последние 10 строк лога:"
        tail -n 10 bot.log
    fi
else
    echo "❌ Бот НЕ ЗАПУЩЕН"
    
    if [ -f "bot.lock" ]; then
        echo "⚠️  Обнаружен старый файл блокировки (бот не работает)"
        echo "Выполните: rm -f bot.lock"
    fi
fi

echo ""
echo "Все Python процессы:"
ps aux | grep python | grep -v grep
