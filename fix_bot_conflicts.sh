#!/bin/bash

# Скрипт для исправления конфликтов ботов
# Автоматически останавливает все экземпляры и запускает только один

echo "🔍 Проверка запущенных ботов..."

# Проверяем количество запущенных ботов
BOT_COUNT=$(ps aux | grep "bot_fondklik_correct.py" | grep -v grep | wc -l)

if [ "$BOT_COUNT" -eq 0 ]; then
    echo "✅ Боты не запущены"
    echo "🚀 Запускаю бота..."
    rm -f bot.lock
    python3 bot_fondklik_correct.py &
    echo "✅ Бот запущен"
elif [ "$BOT_COUNT" -eq 1 ]; then
    echo "✅ Запущен только один бот - все в порядке"
else
    echo "❌ Обнаружено $BOT_COUNT ботов! Исправляю..."
    
    # Останавливаем все боты
    echo "🛑 Останавливаю все боты..."
    pkill -f "bot_fondklik_correct.py"
    
    # Ждем немного
    sleep 2
    
    # Проверяем, остались ли процессы
    REMAINING=$(ps aux | grep "bot_fondklik_correct.py" | grep -v grep | wc -l)
    
    if [ "$REMAINING" -gt 0 ]; then
        echo "⚠️  Некоторые процессы не остановились, принудительно завершаю..."
        ps aux | grep "bot_fondklik_correct.py" | grep -v grep | awk '{print $2}' | xargs kill -9
        sleep 1
    fi
    
    # Удаляем lock файл
    rm -f bot.lock
    
    # Запускаем один бот
    echo "🚀 Запускаю один бот..."
    python3 bot_fondklik_correct.py &
    
    # Проверяем результат
    sleep 3
    FINAL_COUNT=$(ps aux | grep "bot_fondklik_correct.py" | grep -v grep | wc -l)
    
    if [ "$FINAL_COUNT" -eq 1 ]; then
        echo "✅ Проблема исправлена! Запущен только один бот"
    else
        echo "❌ Ошибка! Количество ботов: $FINAL_COUNT"
    fi
fi

echo "📊 Текущее состояние:"
ps aux | grep "bot_fondklik_correct.py" | grep -v grep






