#!/bin/bash
# Скрипт для копирования файлов на VPS (выполняйте на вашем Mac)

VPS_IP="199.217.98.13"

echo "📤 Копирование файлов на VPS..."
echo ""

echo "1️⃣ Копирование Payment API..."
scp -r /Users/roma/Desktop/платежка/* root@${VPS_IP}:/opt/fondklik/payment_api/

echo ""
echo "2️⃣ Копирование главного бота..."
scp -r /Users/roma/Desktop/Fondklik/* root@${VPS_IP}:/opt/fondklik/bot/

echo ""
echo "✅ Файлы скопированы!"
echo ""
echo "Теперь вернитесь к окну SSH и выполните следующие команды:"


