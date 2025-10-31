#!/bin/bash
# =============================================================================
# СКРИПТ КОПИРОВАНИЯ ФАЙЛОВ НА VPS
# Выполните этот скрипт на вашем локальном компьютере
# =============================================================================

VPS_USER="root"
VPS_IP="199.217.98.13"

echo "🚀 Копирование файлов на VPS (${VPS_IP})..."
echo ""

# Создаем директории на VPS
echo "📁 Создание директорий на VPS..."
ssh ${VPS_USER}@${VPS_IP} "mkdir -p /opt/fondklik/payment_api /opt/fondklik/bot /opt/fondklik/logs"

# Копируем Payment API
echo "📤 Копирование Payment API..."
scp -r /Users/roma/Desktop/платежка/* ${VPS_USER}@${VPS_IP}:/opt/fondklik/payment_api/

# Копируем главный бот
echo "📤 Копирование главного бота..."
scp -r /Users/roma/Desktop/Fondklik/* ${VPS_USER}@${VPS_IP}:/opt/fondklik/bot/

echo ""
echo "✅ Файлы скопированы!"
echo ""
echo "Следующий шаг:"
echo "  ssh ${VPS_USER}@${VPS_IP}"
echo "  cd /opt/fondklik/bot"
echo "  bash install_on_vps.sh"


