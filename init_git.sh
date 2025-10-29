#!/bin/bash

echo "🚀 Инициализация Git репозитория для Railway..."
echo ""

# Проверка, что мы в правильной директории
if [ ! -f "bot_fondklik_correct.py" ]; then
    echo "❌ Ошибка: запустите скрипт из папки проекта"
    exit 1
fi

# Инициализация git, если еще не инициализирован
if [ ! -d ".git" ]; then
    echo "📦 Инициализация git..."
    git init
    echo "✅ Git инициализирован"
else
    echo "ℹ️  Git уже инициализирован"
fi

# Проверка .gitignore
if [ ! -f ".gitignore" ]; then
    echo "❌ Ошибка: .gitignore не найден"
    exit 1
fi

echo ""
echo "📝 Добавление файлов..."

# Добавляем только необходимые файлы
git add .gitignore
git add Procfile
git add requirements.txt
git add runtime.txt
git add env_example.txt

# Основной код
git add bot_fondklik_correct.py
git add simple_payment_api.py
git add payment_client.py
git add payment_handlers.py
git add payment_config.py
git add database.py
git add tron_tracker.py
git add config.py

# Документация
git add QUICK_RAILWAY_SETUP.md
git add RAILWAY_DEPLOY_GUIDE.md
git add README_RAILWAY.md
git add DEPLOYMENT_CHECKLIST.md

echo "✅ Файлы добавлены"
echo ""

# Показываем статус
echo "📊 Статус git:"
git status --short
echo ""

# Запрашиваем подтверждение
read -p "Сделать первый коммит? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "Initial commit: Ready for Railway deployment

- ✅ Telegram bot с платежной системой
- ✅ Payment Bot API
- ✅ Интеграция с TRON (USDT TRC20)
- ✅ 3-уровневая реферальная система
- ✅ Админ-панель
- ✅ Автоматическая проверка платежей
- ✅ Настроен для деплоя на Railway"
    
    echo ""
    echo "✅ Коммит создан!"
    echo ""
    
    # Инструкции по созданию GitHub репозитория
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📌 СЛЕДУЮЩИЕ ШАГИ:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1️⃣  Создайте репозиторий на GitHub:"
    echo "   👉 https://github.com/new"
    echo ""
    echo "2️⃣  Назовите его, например: 'fondklik-bot'"
    echo ""
    echo "3️⃣  НЕ добавляйте README, .gitignore или LICENSE"
    echo "   (они уже есть в проекте)"
    echo ""
    echo "4️⃣  После создания выполните команды:"
    echo ""
    echo "   git branch -M main"
    echo "   git remote add origin https://github.com/ВАШ_USERNAME/fondklik-bot.git"
    echo "   git push -u origin main"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "5️⃣  Затем откройте Railway:"
    echo "   👉 https://railway.app"
    echo ""
    echo "6️⃣  New Project → Deploy from GitHub repo"
    echo ""
    echo "7️⃣  Следуйте инструкциям в QUICK_RAILWAY_SETUP.md"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📚 Полная документация: DEPLOYMENT_CHECKLIST.md"
    echo ""
    echo "Удачи! 🚀"
    echo ""
else
    echo "ℹ️  Коммит отменен. Вы можете сделать его позже:"
    echo "   git commit -m 'Initial commit'"
fi

