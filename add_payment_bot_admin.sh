#!/bin/bash
# Скрипт для добавления админа в Payment Bot
# Выполняйте на VPS

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PAYMENT_BOT_DIR="/opt/fondklik/payment_bot"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ДОБАВЛЕНИЕ АДМИНА В PAYMENT BOT${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Ввод ID админа
read -p "Введите ваш Telegram ID (админ): " ADMIN_ID

if [ -z "$ADMIN_ID" ]; then
    echo -e "${RED}❌ ID обязателен!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}[1/3] Добавление в whitelist...${NC}"
cd "${PAYMENT_BOT_DIR}"
source venv/bin/activate

python manage_whitelist.py add "${ADMIN_ID}" 2>/dev/null || python3 <<EOF
from database import Database
db = Database()
db.add_user(${ADMIN_ID}, "admin", "")
print("✅ Пользователь добавлен в whitelist")
EOF

deactivate
echo ""

echo -e "${YELLOW}[2/3] Изменение ID админа в коде...${NC}"
# Заменяем ID админа в коде
sed -i "s/if user_id not in \[123456789\]/if user_id not in [${ADMIN_ID}]/g" private_bot.py

# Проверяем изменения
if grep -q "if user_id not in \[${ADMIN_ID}\]" private_bot.py; then
    echo -e "${GREEN}✅ ID админа изменен${NC}"
else
    echo -e "${YELLOW}⚠️  Не удалось автоматически изменить ID, проверьте вручную${NC}"
fi
echo ""

echo -e "${YELLOW}[3/3] Перезапуск бота...${NC}"
systemctl restart payment-bot.service
sleep 3

if systemctl is-active --quiet payment-bot.service; then
    echo -e "${GREEN}✅ Бот перезапущен${NC}"
else
    echo -e "${RED}❌ Ошибка перезапуска${NC}"
    echo "Проверьте: systemctl status payment-bot.service"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ГОТОВО!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Теперь у вас есть доступ к Payment Bot:"
echo "  - Вы в whitelist"
echo "  - Админские команды доступны"
echo ""
echo "Проверьте в Telegram, бот должен отвечать!"

