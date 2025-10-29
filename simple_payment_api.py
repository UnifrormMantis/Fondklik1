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
    try:
        user_wallet = request.user_wallet
        
        # Получаем самый новый активный кошелек для всех пользователей
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT wallet_address FROM user_wallets 
            WHERE is_active = 1 
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Нет доступных активных кошельков")
        
        active_wallet = result[0]
        
        logger.info(f"Возвращаем актуальный активный кошелек для {user_wallet}: {active_wallet}")
        
        return {
            "success": True,
            "wallet_address": active_wallet
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения кошелька для платежа: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")

@app.post("/check-user-payments")
async def check_user_payments(request: CheckUserPaymentsRequest, api_key: str = Depends(verify_api_key)):
    """Проверить переводы с кошелька пользователя на активный кошелек"""
    try:
        user_wallet = request.user_wallet
        
        # Получаем текущий активный кошелек (тот же, что возвращает /get-payment-wallet)
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT wallet_address FROM user_wallets 
            WHERE is_active = 1 
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {
                "success": True,
                "payments": [],
                "message": "Нет доступных активных кошельков"
            }
        
        active_wallet = result[0]
        
        # Создаем связь для отслеживания платежей (если её еще нет)
        existing_link = db.get_active_wallet_for_user(user_wallet)
        if not existing_link:
            db.create_payment_link(user_wallet, active_wallet)
            logger.info(f"Создана связь для отслеживания платежей: {user_wallet} -> {active_wallet}")
        
        # Получаем все платежи пользователя из базы данных
        payments = db.get_user_payments(user_wallet)
        
        # Фильтруем только подтвержденные платежи
        confirmed_payments = [
            {
                "amount": payment["amount"],
                "tx_hash": payment["tx_hash"],
                "confirmed": payment["confirmed"],
                "timestamp": payment["timestamp"]
            }
            for payment in payments
            if payment["confirmed"]
        ]
        
        logger.info(f"Найдено {len(confirmed_payments)} подтвержденных платежей для {user_wallet} на {active_wallet}")
        
        return {
            "success": True,
            "payments": confirmed_payments
        }
        
    except Exception as e:
        logger.error(f"Ошибка проверки платежей пользователя: {e}")
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
