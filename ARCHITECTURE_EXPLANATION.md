# 🏗️ АРХИТЕКТУРА ВЗАИМОДЕЙСТВИЯ БОТОВ

## 📊 СХЕМА ВЗАИМОДЕЙСТВИЯ

```
┌─────────────────┐         ┌──────────────┐         ┌──────────────┐
│  Fondklik Bot   │────────▶│ Payment API  │◀────────│ Payment Bot  │
│  (Основной бот) │         │  (FastAPI)   │         │ (Админ бот)  │
└─────────────────┘         └──────────────┘         └──────────────┘
       │                           │                           │
       │                           │                           │
       ▼                           ▼                           ▼
┌─────────────────┐         ┌──────────────┐         ┌──────────────┐
│ bot_database.db│         │ payments.db    │         │payment_bot.db │
└─────────────────┘         └──────────────┘         └──────────────┘
```

---

## 🔄 КАК ДОЛЖНО РАБОТАТЬ ВЗАИМОДЕЙСТВИЕ

### 1️⃣ **Payment Bot (Админский бот для управления кошельками)**

**Роль:** Админ управляет кошельками через этого бота

**Что делает:**
- ✅ Админ добавляет кошельки через бота: `/wallet` → "➕ Добавить кошелек"
- ✅ Админ активирует кошелек: выбирает кошелек → "✅ Активировать"
- ✅ **ВСЕ ДЕЙСТВИЯ** сохраняются в **СВОЮ базу** `payment_bot.db`

**База данных:** `payment_bot.db`
- Таблица `user_wallets`: все кошельки админа
- Поле `is_active = 1` означает активный кошелек

**Пример:**
```python
# Payment Bot сохраняет в свою БД:
payment_bot.db:
  user_wallets:
    - wallet_address: "TRealWallet123..."
      is_active: 1  ← АКТИВНЫЙ
    - wallet_address: "TBackupWallet456..."
      is_active: 0
```

---

### 2️⃣ **Payment API (FastAPI - связующее звено)**

**Роль:** Получает запросы от Fondklik Bot и возвращает активный кошелек

**Проблема ТЕКУЩАЯ:** 
- ❌ API ищет кошелек в **своей базе** `payments.db`
- ❌ Но кошельки добавляются в **базу Payment Bot** `payment_bot.db`
- ❌ **БАЗЫ НЕ СИНХРОНИЗИРОВАНЫ!**

**Что должно быть:**
```python
# Вариант 1: API должен читать из базы Payment Bot
@app.post("/get-payment-wallet")
async def get_payment_wallet(...):
    # НЕ payments.db, а payment_bot.db!
    conn = sqlite3.connect("/opt/fondklik/payment_bot/payment_bot.db")
    cursor.execute('''
        SELECT wallet_address FROM user_wallets 
        WHERE is_active = 1 LIMIT 1
    ''')
    # Возвращает активный кошелек из Payment Bot
```

**Или вариант 2:** Синхронизация баз
- Когда админ активирует кошелек в Payment Bot → автоматически копируется в `payments.db`

---

### 3️⃣ **Fondklik Bot (Основной бот для пользователей)**

**Роль:** Пользователи создают депозиты через этого бота

**Что делает:**
1. Пользователь нажимает "💳 Внести депозит" → "💳 Оплатить"
2. Бот вызывает `payment_client.get_payment_wallet(user_wallet)`
3. `payment_client` делает запрос к Payment API:
   ```python
   POST http://127.0.0.1:8001/get-payment-wallet
   Headers: X-API-Key: ...
   Body: {"user_wallet": "TUserWallet123..."}
   ```
4. Payment API должен вернуть активный кошелек из Payment Bot
5. Бот показывает пользователю кошелек для оплаты

**База данных:** `bot_database.db`
- Хранит депозиты пользователей
- Хранит кошельки пользователей (не для приема платежей!)

---

## ❗ ТЕКУЩАЯ ПРОБЛЕМА

```
Payment Bot (активирует кошелек)
    ↓
payment_bot.db: wallet_address="TRealWallet123", is_active=1 ✅

Payment API (ищет кошелек)
    ↓
payments.db: user_wallets пуста или нет активных ❌

Результат:
Fondklik Bot получает: {"success": False} или тестовый кошелек
```

---

## ✅ ПРАВИЛЬНОЕ РЕШЕНИЕ

### **Вариант А: API читает из базы Payment Bot**

**Изменить `simple_payment_api.py`:**
```python
@app.post("/get-payment-wallet")
async def get_payment_wallet(...):
    # Использовать базу Payment Bot вместо payments.db
    PAYMENT_BOT_DB = "/opt/fondklik/payment_bot/payment_bot.db"
    conn = sqlite3.connect(PAYMENT_BOT_DB)
    
    cursor.execute('''
        SELECT wallet_address FROM user_wallets 
        WHERE is_active = 1 
        ORDER BY created_at DESC
        LIMIT 1
    ''')
    
    # Возвращает реальный активный кошелек
```

**Плюсы:**
- ✅ Одна точка истины (Payment Bot)
- ✅ Не нужна синхронизация
- ✅ Всегда актуальные данные

---

### **Вариант Б: Автоматическая синхронизация**

**Когда админ активирует кошелек в Payment Bot:**
```python
# В private_bot.py при активации кошелька:
async def wallet_action_callback(...):
    if action == "activate":
        self.db.set_active_wallet(user_id, wallet_id)  # В payment_bot.db
        
        # ДОПОЛНИТЕЛЬНО: Синхронизировать в Payment API
        sync_to_payment_api(wallet_address)
```

**Создать функцию синхронизации:**
```python
def sync_to_payment_api(wallet_address):
    """Синхронизировать активный кошелек в базу Payment API"""
    api_db = sqlite3.connect("/opt/fondklik/payment_api/payments.db")
    cursor = api_db.cursor()
    
    cursor.execute('''
        UPDATE user_wallets SET is_active = 0;
        INSERT OR REPLACE INTO user_wallets (user_id, wallet_address, is_active)
        VALUES (0, ?, 1)
    ''', (wallet_address,))
    
    api_db.commit()
    api_db.close()
```

**Плюсы:**
- ✅ Payment API остается независимым
- ✅ Можно кэшировать данные

---

## 🎯 РЕКОМЕНДУЕМОЕ РЕШЕНИЕ

**Выбрать Вариант А** - API читает напрямую из базы Payment Bot

**Почему:**
1. ✅ Проще реализовать
2. ✅ Нет дублирования данных
3. ✅ Всегда актуальные данные
4. ✅ Меньше точек отказа

**Нужно изменить только:**
- `simple_payment_api.py`: использовать путь к `payment_bot.db` вместо `payments.db`

---

## 📝 ПРИМЕР ПОЛНОГО ПОТОКА

### Сценарий: Пользователь хочет внести депозит

1. **Админ активирует кошелек в Payment Bot:**
   ```
   Payment Bot → payment_bot.db: 
     UPDATE user_wallets SET is_active = 1 WHERE wallet_address = "TRealWallet123"
   ```

2. **Пользователь в Fondklik Bot:**
   ```
   Нажимает: "💳 Внести депозит" → "30 дней" → "💳 Оплатить"
   ```

3. **Fondklik Bot запрашивает кошелек:**
   ```python
   payment_client.get_payment_wallet("TUserWallet456")
   → POST http://127.0.0.1:8001/get-payment-wallet
   ```

4. **Payment API получает активный кошелек:**
   ```python
   # Читает из payment_bot.db
   SELECT wallet_address FROM user_wallets WHERE is_active = 1
   → "TRealWallet123"
   ```

5. **Fondklik Bot показывает пользователю:**
   ```
   💳 ВНЕСЕНИЕ СРЕДСТВ НА ДЕПОЗИТ
   🏦 Адрес для перевода:
   TRealWallet123... ✅ (РЕАЛЬНЫЙ КОШЕЛЕК!)
   ```

---

## 🔧 ЧТО НУЖНО ИСПРАВИТЬ

1. ✅ Изменить `simple_payment_api.py`:
   - Использовать путь к `payment_bot.db` 
   - Читать активный кошелек оттуда

2. ✅ Убрать зависимость от `payments.db` для кошельков

3. ✅ Проверить, что Payment API имеет доступ к файлу `payment_bot.db`

---

**Это правильная архитектура!** 🎯

