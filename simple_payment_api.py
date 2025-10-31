#!/usr/bin/env python3
"""
Простой API для интеграции платежей
Как у популярных платежных ботов - один API ключ и все работает
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import secrets
import hashlib
from datetime import datetime, timedelta
from database import Database
from tron_tracker import TronTracker
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI(
    title="Simple Payment API",
    description="Простой API для интеграции TRC20 платежей - как у популярных платежных ботов",
    version="2.1.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация
db = Database()
tron_tracker = TronTracker()

# Хранилище API ключей (в реальном проекте используйте базу данных)
api_keys = {}

# Модели данных
class CreatePaymentRequest(BaseModel):
    amount: float
    currency: str = "USDT"
    description: Optional[str] = None
    callback_url: Optional[str] = None

class PaymentResponse(BaseModel):
    success: bool
    payment_id: Optional[str] = None
    wallet_address: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None

class PaymentStatusResponse(BaseModel):
    success: bool
    payment_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    transaction_hash: Optional[str] = None
    error: Optional[str] = None

# Функция проверки API ключа
async def verify_api_key(x_api_key: str = Header(None)):
    """Проверка API ключа"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API ключ не предоставлен")
    
    # Проверяем API ключ в базе данных
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id FROM api_keys 
        WHERE api_key = ? AND is_active = 1
    ''', (x_api_key,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=401, detail="Неверный API ключ")
    
    return result[0]

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Simple Payment API",
        "version": "2.1.0",
        "description": "Простой API для интеграции TRC20 платежей",
        "endpoints": [
            "/create-payment - Создать платеж",
            "/check-payment/{payment_id} - Проверить статус платежа",
            "/get-api-key - Получить API ключ",
            "/get-payment-wallet - Получить кошелек для платежа",
            "/check-user-payments - Проверить платежи пользователя",
            "/docs - Документация"
        ]
    }

@app.get("/get-api-key")
async def get_api_key():
    """Получить API ключ для интеграции"""
    # Генерируем уникальный API ключ
    api_key = secrets.token_urlsafe(32)
    
    # Создаем запись в базе данных
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Создаем таблицу для API ключей если её нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            api_key TEXT PRIMARY KEY,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Сохраняем API ключ
    cursor.execute('''
        INSERT INTO api_keys (api_key, user_id)
        VALUES (?, ?)
    ''', (api_key, 0))  # 0 означает системный ключ
    
    conn.commit()
    conn.close()
    
    # Сохраняем в памяти
    api_keys[api_key] = {
        "user_id": 0,
        "created_at": datetime.now(),
        "is_active": True
    }
    
    return {
        "success": True,
        "api_key": api_key,
        "message": "API ключ создан успешно",
        "usage": {
            "header": "X-API-Key",
            "example": f"X-API-Key: {api_key}"
        }
    }

@app.post("/create-payment", response_model=PaymentResponse)
async def create_payment(
    request: CreatePaymentRequest,
    api_data: dict = Depends(verify_api_key)
):
    """Создать платеж"""
    try:
        # Генерируем уникальный ID платежа
        payment_id = secrets.token_urlsafe(16)
        
        # Получаем адрес кошелька для платежа
        # В реальном проекте здесь должна быть логика получения адреса
        wallet_address = "TYourPaymentWallet1234567890123456789012345"
        
        # Сохраняем платеж в базе данных
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Создаем таблицу для платежей если её нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simple_payments (
                payment_id TEXT PRIMARY KEY,
                amount REAL,
                currency TEXT,
                wallet_address TEXT,
                status TEXT DEFAULT 'pending',
                callback_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                api_key TEXT
            )
        ''')
        
        cursor.execute('''
            INSERT INTO simple_payments 
            (payment_id, amount, currency, wallet_address, callback_url, api_key)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (payment_id, request.amount, request.currency, wallet_address, 
              request.callback_url, api_data.get('api_key', '')))
        
        conn.commit()
        conn.close()
        
        return PaymentResponse(
            success=True,
            payment_id=payment_id,
            wallet_address=wallet_address,
            amount=request.amount,
            currency=request.currency,
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        return PaymentResponse(
            success=False,
            error=str(e)
        )

@app.get("/check-payment/{payment_id}", response_model=PaymentStatusResponse)
async def check_payment(
    payment_id: str,
    api_data: dict = Depends(verify_api_key)
):
    """Проверить статус платежа"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT amount, currency, wallet_address, status, callback_url
            FROM simple_payments 
            WHERE payment_id = ? AND api_key = ?
        ''', (payment_id, api_data.get('api_key', '')))
        
        payment = cursor.fetchone()
        conn.close()
        
        if not payment:
            return PaymentStatusResponse(
                success=False,
                error="Платеж не найден"
            )
        
        amount, currency, wallet_address, status, callback_url = payment
        
        # Если платеж еще pending, проверяем поступления
        if status == "pending":
            try:
                # Проверяем новые транзакции
                new_transfers = tron_tracker.get_new_transfers(wallet_address)
                
                for transfer in new_transfers:
                    # Проверяем, соответствует ли сумма
                    if abs(transfer['amount'] - amount) < 0.01:  # Допуск 0.01 USDT
                        # Обновляем статус платежа
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute('''
                            UPDATE simple_payments 
                            SET status = 'completed', transaction_hash = ?
                            WHERE payment_id = ?
                        ''', (transfer['tx_hash'], payment_id))
                        
                        conn.commit()
                        conn.close()
                        
                        # Отправляем callback если указан
                        if callback_url:
                            await send_callback(callback_url, {
                                "payment_id": payment_id,
                                "status": "completed",
                                "amount": amount,
                                "currency": currency,
                                "transaction_hash": transfer['tx_hash']
                            })
                        
                        return PaymentStatusResponse(
                            success=True,
                            payment_id=payment_id,
                            status="completed",
                            amount=amount,
                            currency=currency,
                            transaction_hash=transfer['tx_hash']
                        )
            except Exception as e:
                logger.error(f"Ошибка проверки платежа: {e}")
        
        return PaymentStatusResponse(
            success=True,
            payment_id=payment_id,
            status=status,
            amount=amount,
            currency=currency
        )
        
    except Exception as e:
        logger.error(f"Ошибка проверки статуса платежа: {e}")
        return PaymentStatusResponse(
            success=False,
            error=str(e)
        )

async def send_callback(url: str, data: dict):
    """Отправка callback уведомления"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, timeout=10) as response:
                logger.info(f"Callback отправлен: {response.status}")
    except Exception as e:
        logger.error(f"Ошибка отправки callback: {e}")

# =============================================================================
# НОВЫЕ ЭНДПОИНТЫ ДЛЯ ИНТЕГРАЦИИ С ОСНОВНЫМ БОТОМ
# =============================================================================

class GetPaymentWalletRequest(BaseModel):
    user_wallet: str

class CheckUserPaymentsRequest(BaseModel):
    user_wallet: str

@app.post("/get-payment-wallet")
async def get_payment_wallet(request: GetPaymentWalletRequest, api_key: str = Depends(verify_api_key)):
    """Получить активный кошелек для приема платежей"""
    import sqlite3
    import os
    
    try:
        user_wallet = request.user_wallet
        
        # Читаем активный кошелек из базы Payment Bot (источник истины)
        # Payment Bot использует payments.db в своей директории
        PAYMENT_BOT_DB_PATHS = [
            os.getenv("PAYMENT_BOT_DB_PATH"),  # Переменная окружения (приоритет)
            "/opt/fondklik/payment_bot/payments.db",  # Основной путь на VPS
            "/opt/fondklik/payment_bot/payment_bot.db",  # Альтернативный путь
            "payment_bot.db",  # Для разработки
            "payments.db"  # Для разработки
        ]
        
        PAYMENT_BOT_DB = None
        for db_path in PAYMENT_BOT_DB_PATHS:
            if db_path and os.path.exists(db_path):
                PAYMENT_BOT_DB = db_path
                break
        
        if not PAYMENT_BOT_DB:
            logger.error("База данных Payment Bot не найдена. Проверенные пути: " + str(PAYMENT_BOT_DB_PATHS))
            raise HTTPException(status_code=500, detail="База данных Payment Bot не найдена")
        
        try:
            conn = sqlite3.connect(PAYMENT_BOT_DB)
            cursor = conn.cursor()
            
            # Проверить существование таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_wallets'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                # Таблица не существует - создать её (Payment Bot должен был создать, но на всякий случай)
                logger.warning(f"Таблица user_wallets не найдена в {PAYMENT_BOT_DB}, создаем...")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_wallets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        wallet_address TEXT NOT NULL,
                        wallet_name TEXT,
                        is_active BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, wallet_address)
                    )
                ''')
                conn.commit()
                logger.info("✅ Таблица user_wallets создана")
            
            cursor.execute('''
                SELECT wallet_address FROM user_wallets 
                WHERE is_active = 1 
                ORDER BY created_at DESC
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                logger.error(f"Нет активных кошельков в Payment Bot (база: {PAYMENT_BOT_DB})")
                raise HTTPException(status_code=404, detail="Нет доступных активных кошельков")
            
            active_wallet = result[0]
            logger.info(f"✅ Возвращаем активный кошелек из Payment Bot ({PAYMENT_BOT_DB}) для {user_wallet}: {active_wallet}")
            
            return {
                "success": True,
                "wallet_address": active_wallet
            }
            
        except sqlite3.Error as db_error:
            logger.error(f"Ошибка доступа к базе Payment Bot: {db_error}")
            raise HTTPException(status_code=500, detail=f"Ошибка доступа к базе данных: {str(db_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
            logger.error(f"Ошибка получения кошелька для платежа: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")

@app.post("/check-user-payments")
async def check_user_payments(request: CheckUserPaymentsRequest, api_key: str = Depends(verify_api_key)):
    """Проверить переводы с кошелька пользователя на активный кошелек
    
    Проверяет по 4 критериям:
    1. Сходится ли кошелек пользователя с того, с которого пришел перевод
    2. Точно ли пришли USDT, а не TRON
    3. Проверка что пришло не меньше 50 USDT
    4. Перевод поступил на активный кошелек
    """
    import sqlite3
    import os
    
    try:
        user_wallet = request.user_wallet.upper().strip()
        
        # Получаем текущий активный кошелек из Payment Bot
        # Payment Bot использует payments.db в своей директории
        PAYMENT_BOT_DB_PATHS = [
            os.getenv("PAYMENT_BOT_DB_PATH"),
            "/opt/fondklik/payment_bot/payments.db",
            "/opt/fondklik/payment_bot/payment_bot.db",
            "payment_bot.db",
            "payments.db"
        ]
        
        PAYMENT_BOT_DB = None
        for db_path in PAYMENT_BOT_DB_PATHS:
            if db_path and os.path.exists(db_path):
                PAYMENT_BOT_DB = db_path
                break
        
        if not PAYMENT_BOT_DB:
            logger.error("База данных Payment Bot не найдена")
            return {
                "success": True,
                "payments": [],
                "message": "База данных Payment Bot не найдена"
            }
        
        conn_bot = sqlite3.connect(PAYMENT_BOT_DB)
        cursor_bot = conn_bot.cursor()
        
        cursor_bot.execute('''
            SELECT wallet_address FROM user_wallets 
            WHERE is_active = 1 
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        
        result = cursor_bot.fetchone()
        conn_bot.close()
        
        if not result:
            return {
                "success": True,
                "payments": [],
                "message": "Нет доступных активных кошельков"
            }
        
        active_wallet = result[0].upper().strip()
        logger.info(f"Проверяем переводы от {user_wallet} на {active_wallet}")
        
        # Получаем последние транзакции активного кошелька через TronTracker
        transactions = tron_tracker.get_trc20_transactions(active_wallet, limit=100)
        
        # Фильтруем транзакции по 4 критериям
        valid_payments = []
        MIN_AMOUNT = 50.0  # Минимум 50 USDT
        
        for tx in transactions:
            try:
                # Парсим транзакцию
                parsed = tron_tracker.parse_trc20_transfer(tx)
                if not parsed:
                    continue
                
                from_address = parsed.get('from_address', '').upper().strip()
                to_address = parsed.get('to_address', '').upper().strip()
                amount = parsed.get('amount', 0)
                tx_hash = parsed.get('tx_hash', '')
                
                # КРИТЕРИЙ 1: Сходится ли кошелек пользователя
                if from_address != user_wallet:
                    continue
                
                # КРИТЕРИЙ 2: Точно ли пришли USDT (проверяем что parse_trc20_transfer вернул данные - значит это USDT)
                # Проверка USDT уже выполнена в parse_trc20_transfer (фильтрует по контракту)
                
                # КРИТЕРИЙ 4: Перевод поступил на активный кошелек
                if to_address != active_wallet:
                    continue
                
                # КРИТЕРИЙ 3: Не меньше 50 USDT
                if amount < MIN_AMOUNT:
                    logger.info(f"Платеж отклонен: сумма {amount} < {MIN_AMOUNT} USDT")
                    continue
                
                # КРИТЕРИЙ 4: Перевод на активный кошелек (уже проверили выше)
                # Все критерии выполнены!
                valid_payments.append({
                    "amount": amount,
                    "tx_hash": tx_hash,
                    "from_address": from_address,
                    "to_address": to_address,
                    "confirmed": True,
                    "timestamp": parsed.get('timestamp', datetime.now().isoformat())
                })
                
                logger.info(f"✅ Найден валидный платеж: {amount} USDT от {from_address} на {to_address}, tx: {tx_hash}")
                
            except Exception as e:
                logger.error(f"Ошибка парсинга транзакции: {e}")
                continue
        
        # Сохраняем найденные платежи в базу для истории
        if valid_payments:
            conn_api = db.get_connection()
            cursor_api = conn_api.cursor()
            
            for payment in valid_payments:
                # Проверяем, не добавлен ли уже этот платеж
                cursor_api.execute('''
                    SELECT id FROM payment_tracking 
                    WHERE tx_hash = ? AND user_wallet = ?
                ''', (payment['tx_hash'], user_wallet))
                
                if not cursor_api.fetchone():
                    cursor_api.execute('''
                        INSERT INTO payment_tracking 
                        (user_wallet, active_wallet, amount, tx_hash, confirmed)
                        VALUES (?, ?, ?, ?, 1)
                    ''', (user_wallet, active_wallet, payment['amount'], payment['tx_hash']))
            
            conn_api.commit()
            conn_api.close()
        
        logger.info(f"Найдено {len(valid_payments)} валидных платежей для {user_wallet}")
        
        return {
            "success": True,
            "payments": valid_payments,
            "active_wallet": active_wallet
        }
        
    except Exception as e:
        logger.error(f"Ошибка проверки платежей пользователя: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")

@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0"
    }

if __name__ == "__main__":
    # Запуск сервера
    import os
    port = int(os.getenv("PORT", 8001))  # Railway передаст порт через переменную PORT
    
    uvicorn.run(
        "simple_payment_api:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # На продакшене отключаем reload
        log_level="info"
    )
