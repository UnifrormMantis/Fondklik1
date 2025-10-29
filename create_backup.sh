#!/bin/bash

# Скрипт для создания резервных копий ботов

echo "🔄 СОЗДАНИЕ РЕЗЕРВНОЙ КОПИИ"
echo "=========================="

# Получаем текущую дату и время
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Создаем резервную копию основного бота
if [ -f "bot_fondklik_correct.py" ]; then
    BACKUP_NAME="bot_fondklik_correct_backup_${TIMESTAMP}.py"
    cp bot_fondklik_correct.py "$BACKUP_NAME"
    echo "✅ Создана резервная копия: $BACKUP_NAME"
else
    echo "❌ Файл bot_fondklik_correct.py не найден"
fi

# Показываем все резервные копии
echo ""
echo "📋 Все резервные копии:"
ls -la bot_fondklik_correct_backup_*.py 2>/dev/null | tail -5

echo ""
echo "💡 Для восстановления используйте:"
echo "   cp bot_fondklik_correct_backup_YYYYMMDD_HHMMSS.py bot_fondklik_correct.py"








