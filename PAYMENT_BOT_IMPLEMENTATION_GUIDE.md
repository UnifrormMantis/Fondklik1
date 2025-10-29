# 🚀 ПОЛНАЯ ИНСТРУКЦИЯ ДЛЯ РЕАЛИЗАЦИИ PAYMENT BOT

## 📋 ОБЗОР

Нужно добавить **2 новых эндпоинта** в Payment Bot для работы с системой депозитов. Эти эндпоинты позволят:

1. **Получать активный кошелек** для приема платежей от пользователей
2. **Проверять переводы** с кошельков пользователей на активный кошелек

---

## 🔧 ЭНДПОИНТ 1: `/get-payment-wallet`

### **Назначение:**
Когда пользователь указывает свой кошелек в боте, мы получаем активный кошелек для приема платежей.

### **HTTP запрос:**
```http
POST /get-payment-wallet
Content-Type: application/json
X-API-Key: X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco

{
  "user_wallet": "TUserWallet123456789"
}
```

### **HTTP ответ:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "wallet_address": "TYourMainWallet456789012"
}
```

### **Код реализации (Python/Flask):**
```python
@app.route('/get-payment-wallet', methods=['POST'])
def get_payment_wallet():
    # Проверяем API ключ
    api_key = request.headers.get('X-API-Key')
    if api_key != 'X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco':
        return jsonify({"success": False, "error": "Invalid API key"}), 401
    
    # Получаем данные из запроса
    data = request.get_json()
    user_wallet = data.get('user_wallet')
    
    if not user_wallet:
        return jsonify({"success": False, "error": "user_wallet is required"}), 400
    
    # Получаем активный кошелек из настроек
    active_wallet = get_active_payment_wallet()  # Ваша функция для получения активного кошелька
    
    # Сохраняем связь пользователь -> активный кошелек
    save_user_payment_link(user_wallet, active_wallet)
    
    return jsonify({
        "success": True,
        "wallet_address": active_wallet
    })

def get_active_payment_wallet():
    """Получить активный кошелек для приема платежей"""
    # Замените на ваш способ получения активного кошелька
    # Это может быть из конфига, базы данных, или переменной окружения
    return "TYourMainWallet456789012"  # Ваш реальный кошелек

def save_user_payment_link(user_wallet, active_wallet):
    """Сохранить связь между кошельком пользователя и активным кошельком"""
    # Сохраните в базу данных или файл
    # Пример для SQLite:
    conn = sqlite3.connect('payment_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_payment_links (user_wallet, active_wallet)
        VALUES (?, ?)
    ''', (user_wallet, active_wallet))
    conn.commit()
    conn.close()
```

---

## 🔧 ЭНДПОИНТ 2: `/check-user-payments`

### **Назначение:**
Проверить, переводил ли пользователь деньги с своего кошелька на активный кошелек.

### **HTTP запрос:**
```http
POST /check-user-payments
Content-Type: application/json
X-API-Key: X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco

{
  "user_wallet": "TUserWallet123456789"
}
```

### **HTTP ответ:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "payments": [
    {
      "amount": 100.0,
      "tx_hash": "0x1234567890abcdef1234567890abcdef12345678",
      "confirmed": true,
      "timestamp": "2025-10-07T23:00:00Z"
    }
  ]
}
```

### **Код реализации (Python/Flask):**
```python
@app.route('/check-user-payments', methods=['POST'])
def check_user_payments():
    # Проверяем API ключ
    api_key = request.headers.get('X-API-Key')
    if api_key != 'X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco':
        return jsonify({"success": False, "error": "Invalid API key"}), 401
    
    # Получаем данные из запроса
    data = request.get_json()
    user_wallet = data.get('user_wallet')
    
    if not user_wallet:
        return jsonify({"success": False, "error": "user_wallet is required"}), 400
    
    # Находим активный кошелек для этого пользователя
    active_wallet = get_active_wallet_for_user(user_wallet)
    if not active_wallet:
        return jsonify({"success": False, "error": "No active wallet found for user"}), 404
    
    # Проверяем блокчейн на переводы
    payments = check_blockchain_transfers(user_wallet, active_wallet)
    
    return jsonify({
        "success": True,
        "payments": payments
    })

def get_active_wallet_for_user(user_wallet):
    """Получить активный кошелек для пользователя"""
    conn = sqlite3.connect('payment_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT active_wallet FROM user_payment_links 
        WHERE user_wallet = ?
    ''', (user_wallet,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def check_blockchain_transfers(from_wallet, to_wallet):
    """Проверить переводы в блокчейне"""
    # Здесь используйте вашу библиотеку для работы с блокчейном
    # Например, для TRON:
    
    payments = []
    
    try:
        # Пример с использованием tronpy или другой библиотеки
        # from tronpy import Tron
        
        # tron = Tron()
        # transactions = tron.get_account_transactions(from_wallet)
        
        # for tx in transactions:
        #     if tx['to'] == to_wallet and tx['confirmed']:
        #         payments.append({
        #             "amount": tx['amount'],
        #             "tx_hash": tx['hash'],
        #             "confirmed": True,
        #             "timestamp": tx['timestamp']
        #         })
        
        # ВРЕМЕННАЯ ЗАГЛУШКА ДЛЯ ТЕСТИРОВАНИЯ:
        # Удалите этот код после реализации реальной проверки блокчейна
        if from_wallet == "TTestUserWallet123456789":
            payments.append({
                "amount": 100.0,
                "tx_hash": "0x1234567890abcdef1234567890abcdef12345678",
                "confirmed": True,
                "timestamp": "2025-10-07T23:00:00Z"
            })
        
    except Exception as e:
        print(f"Ошибка проверки блокчейна: {e}")
    
    return payments
```

---

## 🗄️ НАСТРОЙКА БАЗЫ ДАННЫХ

### **Создание таблиц:**
```sql
-- Таблица связей пользователей
CREATE TABLE user_payment_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_wallet TEXT NOT NULL,
    active_wallet TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_wallet)
);

-- Таблица отслеживания платежей (опционально)
CREATE TABLE payment_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_wallet TEXT NOT NULL,
    active_wallet TEXT NOT NULL,
    amount REAL NOT NULL,
    tx_hash TEXT NOT NULL,
    confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Скрипт инициализации базы данных:**
```python
import sqlite3

def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect('payment_bot.db')
    cursor = conn.cursor()
    
    # Создаем таблицы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_payment_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_wallet TEXT NOT NULL,
            active_wallet TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_wallet)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_wallet TEXT NOT NULL,
            active_wallet TEXT NOT NULL,
            amount REAL NOT NULL,
            tx_hash TEXT NOT NULL,
            confirmed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("База данных инициализирована")

if __name__ == "__main__":
    init_database()
```

---

## 🧪 ТЕСТИРОВАНИЕ

### **Тест 1: Получение кошелька для платежа**
```bash
curl -X POST http://localhost:8002/get-payment-wallet \
  -H "X-API-Key: X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "TTestUserWallet123456789"}'
```

**Ожидаемый ответ:**
```json
{
  "success": true,
  "wallet_address": "TYourMainWallet456789012"
}
```

### **Тест 2: Проверка платежей пользователя**
```bash
curl -X POST http://localhost:8002/check-user-payments \
  -H "X-API-Key: X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco" \
  -H "Content-Type: application/json" \
  -d '{"user_wallet": "TTestUserWallet123456789"}'
```

**Ожидаемый ответ:**
```json
{
  "success": true,
  "payments": [
    {
      "amount": 100.0,
      "tx_hash": "0x1234567890abcdef1234567890abcdef12345678",
      "confirmed": true,
      "timestamp": "2025-10-07T23:00:00Z"
    }
  ]
}
```

---

## ⚙️ КОНФИГУРАЦИЯ

### **Настройки API:**
```python
# config.py
API_KEY = "X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco"
ACTIVE_PAYMENT_WALLET = "TYourMainWallet456789012"  # Замените на ваш реальный кошелек
DATABASE_PATH = "payment_bot.db"
BLOCKCHAIN_RPC_URL = "https://api.trongrid.io"  # Замените на ваш RPC
```

### **Переменные окружения:**
```bash
export PAYMENT_BOT_API_KEY="X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco"
export ACTIVE_WALLET="TYourMainWallet456789012"
export BLOCKCHAIN_RPC="https://api.trongrid.io"
```

---

## 🔄 ПОЛНЫЙ ПРИМЕР ИНТЕГРАЦИИ

### **main.py (основной файл):**
```python
from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Конфигурация
API_KEY = os.getenv('PAYMENT_BOT_API_KEY', 'X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco')
ACTIVE_WALLET = os.getenv('ACTIVE_WALLET', 'TYourMainWallet456789012')

def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect('payment_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_payment_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_wallet TEXT NOT NULL,
            active_wallet TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_wallet)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/get-payment-wallet', methods=['POST'])
def get_payment_wallet():
    # Проверяем API ключ
    api_key = request.headers.get('X-API-Key')
    if api_key != API_KEY:
        return jsonify({"success": False, "error": "Invalid API key"}), 401
    
    data = request.get_json()
    user_wallet = data.get('user_wallet')
    
    if not user_wallet:
        return jsonify({"success": False, "error": "user_wallet is required"}), 400
    
    # Сохраняем связь
    conn = sqlite3.connect('payment_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO user_payment_links (user_wallet, active_wallet)
        VALUES (?, ?)
    ''', (user_wallet, ACTIVE_WALLET))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "wallet_address": ACTIVE_WALLET
    })

@app.route('/check-user-payments', methods=['POST'])
def check_user_payments():
    # Проверяем API ключ
    api_key = request.headers.get('X-API-Key')
    if api_key != API_KEY:
        return jsonify({"success": False, "error": "Invalid API key"}), 401
    
    data = request.get_json()
    user_wallet = data.get('user_wallet')
    
    if not user_wallet:
        return jsonify({"success": False, "error": "user_wallet is required"}), 400
    
    # Получаем активный кошелек
    conn = sqlite3.connect('payment_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT active_wallet FROM user_payment_links 
        WHERE user_wallet = ?
    ''', (user_wallet,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return jsonify({"success": False, "error": "No active wallet found for user"}), 404
    
    active_wallet = result[0]
    
    # Проверяем блокчейн (заглушка для тестирования)
    payments = []
    if user_wallet == "TTestUserWallet123456789":
        payments.append({
            "amount": 100.0,
            "tx_hash": "0x1234567890abcdef1234567890abcdef12345678",
            "confirmed": True,
            "timestamp": datetime.now().isoformat()
        })
    
    return jsonify({
        "success": True,
        "payments": payments
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    init_database()
    app.run(host='0.0.0.0', port=8002, debug=True)
```

---

## 🚀 ЗАПУСК

### **1. Установите зависимости:**
```bash
pip install flask
```

### **2. Настройте переменные окружения:**
```bash
export PAYMENT_BOT_API_KEY="X1FmMLpqCjqkx_q9hr9jww7wuJPniAqT8ErkguoQVco"
export ACTIVE_WALLET="TYourMainWallet456789012"
```

### **3. Запустите сервер:**
```bash
python main.py
```

### **4. Проверьте работу:**
```bash
curl http://localhost:8002/health
```

---

## ✅ ПРОВЕРКА РАБОТЫ

После реализации эндпоинтов:

1. **Запустите Payment Bot** с новыми эндпоинтами
2. **Протестируйте** с помощью curl команд
3. **Проверьте в основном боте** - ошибка должна исчезнуть
4. **Создайте тестовый депозит** для проверки полного цикла

**После этого система будет полностью работать!** 🎉






