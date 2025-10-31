# 🚀 ДЕПЛОЙ НА НОВЫЙ VPS - ПОШАГОВАЯ ИНСТРУКЦИЯ

## 📋 ПЕРЕД НАЧАЛОМ

Вам нужны:
- ✅ IP адрес нового VPS
- ✅ Логин для SSH (обычно `root`)
- ✅ Пароль или SSH ключ
- ✅ Токен Telegram бота

---

## 🎯 ШАГ 1: КОПИРОВАНИЕ ФАЙЛОВ НА VPS

**Выполните на вашем локальном компьютере:**

```bash
# ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ:
VPS_USER="root"
VPS_IP="ВАШ_IP_АДРЕС"  # например: 199.217.99.119

# 1. Создаем директории на VPS
ssh ${VPS_USER}@${VPS_IP} "mkdir -p /opt/fondklik/payment_api /opt/fondklik/bot /opt/fondklik/logs"

# 2. Копируем Payment API (из папки "платежка")
echo "Копирование Payment API..."
scp -r /Users/roma/Desktop/платежка/* ${VPS_USER}@${VPS_IP}:/opt/fondklik/payment_api/

# 3. Копируем главный бот (из папки "Fondklik")
echo "Копирование главного бота..."
scp -r /Users/roma/Desktop/Fondklik/* ${VPS_USER}@${VPS_IP}:/opt/fondklik/bot/

echo "✅ Файлы скопированы!"
```

**Или используйте rsync (быстрее, поддерживает докачку):**

```bash
VPS_USER="root"
VPS_IP="ВАШ_IP_АДРЕС"

# Копирование через rsync
rsync -avz --progress /Users/roma/Desktop/платежка/ ${VPS_USER}@${VPS_IP}:/opt/fondklik/payment_api/
rsync -avz --progress /Users/roma/Desktop/Fondklik/ ${VPS_USER}@${VPS_IP}:/opt/fondklik/bot/

echo "✅ Файлы скопированы!"
```

---

## 🎯 ШАГ 2: ПОДКЛЮЧЕНИЕ К VPS И УСТАНОВКА

**Подключитесь к VPS:**

```bash
ssh root@ВАШ_IP_АДРЕС
```

**На VPS выполните все команды подряд:**

```bash
# Переходим в директорию бота
cd /opt/fondklik/bot

# Запускаем скрипт установки
bash install_on_vps.sh
```

**Скрипт спросит токен бота - введите его когда попросит.**

---

## 🎯 ШАГ 3: ПРОВЕРКА

**После завершения установки проверьте:**

```bash
# Проверка статуса Payment API
sudo systemctl status payment-api.service

# Проверка статуса бота
sudo systemctl status fondklik-bot.service

# Проверка здоровья API
curl http://localhost:8001/health

# Просмотр логов (если есть ошибки)
sudo journalctl -u payment-api.service -n 30 --no-pager
sudo journalctl -u fondklik-bot.service -n 30 --no-pager
```

---

## ✅ ЕСЛИ ВСЁ РАБОТАЕТ

В Telegram боте:
1. Нажмите **"Внести депозит"** → **"Оплатить"**
2. Должен показаться актуальный кошелёк из Payment API
3. Нажмите **"Проверить платеж"**
4. Должен показаться статус платежа

---

## 🐛 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

**Пришлите результат этих команд:**

```bash
# Статус сервисов (первые 20 строк каждого)
sudo systemctl status payment-api.service --no-pager -l | head -20
sudo systemctl status fondklik-bot.service --no-pager -l | head -20

# Проверка здоровья API
curl -v http://localhost:8001/health

# Проверка запущенных процессов
ps aux | grep python
```

---

## 🔧 РУЧНАЯ УСТАНОВКА (если скрипт не работает)

Если скрипт `install_on_vps.sh` не работает, выполните вручную:

```bash
# 1. Установка системных зависимостей
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv curl sqlite3

# 2. Создание виртуальных окружений
cd /opt/fondklik/payment_api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

cd /opt/fondklik/bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# 3. Получите токен бота
read -p "Введите TELEGRAM_BOT_TOKEN: " BOT_TOKEN

# 4. Создание .env для бота
cat > /opt/fondklik/bot/.env <<EOF
TELEGRAM_BOT_TOKEN=${BOT_TOKEN}
PAYMENT_API_URL=http://127.0.0.1:8001
EOF

# 5. Создание systemd сервисов
# (скопируйте содержимое из VPS_DEPLOY_INSTRUCTIONS.md)

# 6. Запуск
sudo systemctl enable payment-api.service
sudo systemctl start payment-api.service
sleep 5
sudo systemctl enable fondklik-bot.service
sudo systemctl start fondklik-bot.service
```

---

## 📞 ПОМОЩЬ

Если что-то не работает - пришлите вывод команд из раздела "ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ", и я помогу исправить!


