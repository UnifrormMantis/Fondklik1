#!/bin/bash
# Остановка всей системы: БОТ + МОНИТОР

CURRENT_DIR="/Users/roma/Desktop/Fondklik"

echo "═══════════════════════════════════════════════════════"
echo "     🛑 ОСТАНОВКА СИСТЕМЫ FONDKLIK BOT"
echo "═══════════════════════════════════════════════════════"
echo ""

# 1. Останавливаем монитор
echo "1️⃣  Останавливаю систему мониторинга..."
if [ -f "$CURRENT_DIR/monitor.pid" ]; then
    MONITOR_PID=$(cat "$CURRENT_DIR/monitor.pid")
    if ps -p $MONITOR_PID > /dev/null 2>&1; then
        kill $MONITOR_PID 2>/dev/null
        sleep 1
        # Если не остановился - принудительно
        if ps -p $MONITOR_PID > /dev/null 2>&1; then
            kill -9 $MONITOR_PID 2>/dev/null
        fi
        echo "   ✅ Монитор остановлен"
    else
        echo "   ℹ️  Монитор не был запущен"
    fi
    rm -f "$CURRENT_DIR/monitor.pid"
else
    echo "   ℹ️  Монитор не был запущен"
fi
echo ""

# 2. Останавливаем все боты
echo "2️⃣  Останавливаю все боты..."
BOTS_RUNNING=$(ps aux | grep "python.*bot.*\.py" | grep -v grep | grep -v monitor | wc -l)
if [ "$BOTS_RUNNING" -gt 0 ]; then
    pkill -9 -f "python.*bot.*\.py" 2>/dev/null
    sleep 2
    echo "   ✅ Все боты остановлены ($BOTS_RUNNING шт.)"
else
    echo "   ℹ️  Боты не были запущены"
fi
echo ""

# 3. Очищаем блокировку
echo "3️⃣  Очищаю блокировки..."
cd "$CURRENT_DIR"
rm -f bot.lock
echo "   ✅ Блокировка очищена"
echo ""

# 4. Проверяем что все остановлено
echo "═══════════════════════════════════════════════════════"
echo "              ✅ ВСЕ ОСТАНОВЛЕНО"
echo "═══════════════════════════════════════════════════════"
echo ""

# Проверка
BOT_COUNT=$(ps aux | grep "python.*bot.*\.py" | grep -v grep | grep -v monitor | wc -l)
if [ "$BOT_COUNT" -eq 0 ]; then
    echo "✅ Ботов запущено: 0"
else
    echo "⚠️  Ботов запущено: $BOT_COUNT"
    echo "   Возможно нужно остановить вручную"
fi
echo ""
echo "═══════════════════════════════════════════════════════"

