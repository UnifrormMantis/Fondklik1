#!/bin/bash
# Добавление админа 8489431460 в Payment Bot
# Выполняйте на VPS

ADMIN_ID=8489431460
PAYMENT_BOT_DIR="/opt/fondklik/payment_bot"

echo "🔧 Добавление админа ${ADMIN_ID} в Payment Bot..."
echo ""

# 1. Добавление в whitelist
echo "[1/3] Добавление в whitelist..."
cd "${PAYMENT_BOT_DIR}"
source venv/bin/activate

python manage_whitelist.py add ${ADMIN_ID} 2>/dev/null || python3 <<EOF
from database import Database
db = Database()
db.add_user(${ADMIN_ID}, "admin", "")
print("✅ Пользователь ${ADMIN_ID} добавлен в whitelist")
EOF

deactivate

# 2. Изменение ID админа в коде
echo ""
echo "[2/3] Изменение ID админа в коде..."
sed -i "s/if user_id not in \[123456789\]/if user_id not in [${ADMIN_ID}]/g" private_bot.py

# Проверка изменений
if grep -q "if user_id not in \[${ADMIN_ID}\]" private_bot.py; then
    echo "✅ ID админа изменен на ${ADMIN_ID}"
else
    echo "⚠️  Проверьте изменения вручную"
    grep -n "if user_id not in" private_bot.py | head -3
fi

# 3. Перезапуск бота
echo ""
echo "[3/3] Перезапуск бота..."
systemctl restart payment-bot.service
sleep 3

# Проверка
if systemctl is-active --quiet payment-bot.service; then
    echo "✅ Бот перезапущен успешно"
    echo ""
    echo "Админ ${ADMIN_ID} теперь имеет доступ к командам:"
    echo "  /admin_add_user <user_id>"
    echo "  /admin_remove_user <user_id>"
    echo "  /admin_list_users"
else
    echo "❌ Ошибка перезапуска"
    systemctl status payment-bot.service --no-pager -l | head -10
fi

