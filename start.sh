#!/bin/bash

# Запускаем Payment API в фоне
python3 simple_payment_api.py &

# Ждем 5 секунд пока Payment API запустится
sleep 5

# Запускаем Payment Bot (управление кошельками) в фоне
(cd payment_bot && python3 main.py) &

# Ждем 3 секунды
sleep 3

# Запускаем основной FondKlik Bot
python3 bot_fondklik_correct.py

