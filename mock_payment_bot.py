#!/usr/bin/env python3
"""
Мок Payment Bot для тестирования ротации кошельков
"""

from flask import Flask, request, jsonify
import time
import threading
from datetime import datetime

app = Flask(__name__)

# Два кошелька для тестирования
WALLET_1 = "TWJ5wQPnJTk2keYXjEgf19i17ZzACBY4Mx"
WALLET_2 = "TRpxhgJ9izoZ56iHJ6gkWwvuStaMeCTisS"

# Текущий активный кошелек
current_wallet = WALLET_1
start_time = time.time()

def rotate_wallet():
    """Функция для ротации кошелька каждые 20 секунд"""
    global current_wallet
    while True:
        time.sleep(20)  # Ждем 20 секунд
        current_wallet = WALLET_2 if current_wallet == WALLET_1 else WALLET_1
        print(f"🔄 Кошелек изменен на: {current_wallet} в {datetime.now().strftime('%H:%M:%S')}")

@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья сервиса"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "current_wallet": current_wallet
    })

@app.route('/wallet-info', methods=['GET'])
def wallet_info():
    """Получение информации о кошельке"""
    elapsed_time = time.time() - start_time
    return jsonify({
        "success": True,
        "wallet_address": current_wallet,
        "balance": 0.908897,
        "currency": "USDT",
        "message": "Информация о кошельке для приема платежей",
        "elapsed_time": round(elapsed_time, 2),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/get-payment-wallet', methods=['POST'])
def get_payment_wallet():
    """Получение кошелька для платежа"""
    data = request.get_json()
    user_wallet = data.get('user_wallet', '')
    
    return jsonify({
        "success": True,
        "wallet_address": current_wallet,
        "user_wallet": user_wallet,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 ЗАПУСК МОК PAYMENT BOT")
    print("=" * 50)
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💰 Начальный кошелек: {current_wallet}")
    print(f"🔄 Ротация каждые 20 секунд")
    print(f"🌐 Порт: 8002")
    print()
    
    # Запускаем ротацию кошельков в отдельном потоке
    rotation_thread = threading.Thread(target=rotate_wallet, daemon=True)
    rotation_thread.start()
    
    # Запускаем Flask сервер
    app.run(host='0.0.0.0', port=8002, debug=False)





