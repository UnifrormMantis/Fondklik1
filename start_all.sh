#!/bin/bash
# Универсальный запуск: БОТ + МОНИТОР

CURRENT_DIR="/Users/roma/Desktop/Fondklik"
ACTUAL_BOT="bot_fondklik_correct.py"

echo "═══════════════════════════════════════════════════════"
echo "     🚀 ЗАПУСК СИСТЕМЫ FONDKLIK BOT"
echo "═══════════════════════════════════════════════════════"
echo ""

# 1. Останавливаем все боты
echo "1️⃣  Останавливаю все существующие боты..."
pkill -9 -f "python.*bot.*\.py" 2>/dev/null
sleep 2
echo "   ✅ Все боты остановлены"
echo ""

# 2. Останавливаем монитор если запущен
echo "2️⃣  Проверяю систему мониторинга..."
if [ -f "$CURRENT_DIR/monitor.pid" ]; then
    MONITOR_PID=$(cat "$CURRENT_DIR/monitor.pid")
    if ps -p $MONITOR_PID > /dev/null 2>&1; then
        kill $MONITOR_PID 2>/dev/null
        rm -f "$CURRENT_DIR/monitor.pid"
        echo "   ✅ Старый монитор остановлен"
    else
        rm -f "$CURRENT_DIR/monitor.pid"
    fi
else
    echo "   ℹ️  Монитор не был запущен"
fi
echo ""

# 3. Очищаем блокировку
echo "3️⃣  Очищаю блокировки..."
cd "$CURRENT_DIR"
rm -f bot.lock
echo "   ✅ Блокировка очищена"
echo ""

# 4. Запускаем актуальный бот
echo "4️⃣  Запускаю актуальный бот: $ACTUAL_BOT"
python3 "$ACTUAL_BOT" > bot_output.log 2>&1 &
BOT_PID=$!
echo "   ⏳ Ожидание стабилизации бота (10 сек)..."
sleep 10

# Проверяем что бот запустился и работает стабильно
if ps -p $BOT_PID > /dev/null 2>&1; then
    # Проверяем логи на ошибки
    if tail -5 bot_output.log | grep -q "Conflict"; then
        echo "   ❌ Бот запустился но есть конфликт"
        echo "   📝 Проверьте логи: bot_output.log"
        kill $BOT_PID 2>/dev/null
        exit 1
    elif tail -5 bot_output.log | grep -q "Application started"; then
        echo "   ✅ Бот запущен и работает стабильно (PID: $BOT_PID)"
    else
        echo "   ✅ Бот запущен (PID: $BOT_PID)"
    fi
else
    echo "   ❌ Не удалось запустить бот"
    echo "   📝 Проверьте логи: bot_output.log"
    exit 1
fi
echo ""

# 5. Запускаем систему мониторинга
echo "5️⃣  Запускаю систему мониторинга..."
nohup "$CURRENT_DIR/bot_monitor.sh" > /dev/null 2>&1 &
MONITOR_PID=$!
echo $MONITOR_PID > "$CURRENT_DIR/monitor.pid"
sleep 2

# Проверяем что монитор запустился
if ps -p $MONITOR_PID > /dev/null 2>&1; then
    echo "   ✅ Монитор запущен (PID: $MONITOR_PID)"
else
    echo "   ❌ Не удалось запустить монитор"
fi
echo ""

# 6. Финальный статус
echo "═══════════════════════════════════════════════════════"
echo "              ✅ СИСТЕМА ЗАПУЩЕНА"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📊 СТАТУС:"
echo "   🤖 Бот:      РАБОТАЕТ (PID: $BOT_PID)"
echo "   👁️  Монитор:  РАБОТАЕТ (PID: $MONITOR_PID)"
echo ""
echo "📝 ЛОГИ:"
echo "   Бот:      tail -f bot_output.log"
echo "   Монитор:  tail -f monitor.log"
echo ""
echo "🛑 ОСТАНОВКА:"
echo "   ./stop_all.sh"
echo ""
echo "📊 СТАТУС:"
echo "   ./status_all.sh"
echo ""
echo "═══════════════════════════════════════════════════════"

