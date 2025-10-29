#!/bin/bash

# Скрипт для тестирования обнаружения ошибок 409 Conflict

echo "🧪 ТЕСТ ОБНАРУЖЕНИЯ ОШИБОК 409 CONFLICT"
echo "========================================"

# Создаем тестовый лог-файл с ошибкой
echo "📄 Создаю тестовый лог-файл с ошибкой 409 Conflict..."

cat > test_conflict.log << EOF
2025-10-07 13:35:16,342 - telegram.ext.Application - ERROR - No error handlers are registered, logging exception.
Traceback (most recent call last):
  File "/Users/roma/Library/Python/3.13/lib/python/site-packages/telegram/ext/_utils/networkloop.py", line 134, in network_retry_loop
    await do_action()
  File "/Users/roma/Library/Python/3.13/lib/python/site-packages/telegram/ext/_utils/networkloop.py", line 127, in do_action
    action_cb_task.result()
telegram.error.Conflict: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
EOF

echo "✅ Тестовый лог-файл создан: test_conflict.log"
echo ""
echo "🔍 Теперь автоматический менеджер должен обнаружить эту ошибку"
echo "   и запустить проверку ботов в течение 2-10 секунд"
echo ""
echo "📋 Для проверки логов менеджера:"
echo "   tail -f bot_auto_manager.log"
echo ""
echo "🗑️ Для удаления тестового файла:"
echo "   rm test_conflict.log"








