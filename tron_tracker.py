import requests
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import config

class TronTracker:
    def __init__(self):
        self.api_url = config.TRON_API_URL
        self.api_key = config.TRON_API_KEY
        self.headers = {
            'TRON-PRO-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        } if self.api_key else {'Content-Type': 'application/json'}
    
    def get_account_info(self, address: str) -> Optional[Dict]:
        """Получить информацию об аккаунте"""
        try:
            url = f"{self.api_url}/v1/accounts/{address}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка получения информации об аккаунте: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Ошибка при запросе к Tron API: {e}")
            return None
    
    def get_trc20_transactions(self, address: str, limit: int = 50) -> List[Dict]:
        """Получить TRC20 транзакции для адреса"""
        try:
            url = f"{self.api_url}/v1/accounts/{address}/transactions/trc20"
            params = {
                'limit': limit,
                'contract_address': config.USDT_CONTRACT_ADDRESS
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            else:
                print(f"Ошибка получения транзакций: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Ошибка при запросе транзакций: {e}")
            return []
    
    def get_transaction_details(self, tx_hash: str) -> Optional[Dict]:
        """Получить детали транзакции по хешу"""
        try:
            url = f"{self.api_url}/v1/transactions/{tx_hash}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ошибка получения деталей транзакции: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Ошибка при запросе деталей транзакции: {e}")
            return None
    
    def parse_trc20_transfer(self, transaction: Dict) -> Optional[Dict]:
        """Парсинг TRC20 transfer события"""
        try:
            # Получаем детали транзакции
            tx_hash = transaction.get('transaction_id')
            tx_details = self.get_transaction_details(tx_hash)
            
            if not tx_details:
                return None
            
            # Ищем TRC20 transfer события
            for log in tx_details.get('raw_data', {}).get('contract', []):
                if log.get('type') == 'TriggerSmartContract':
                    parameter = log.get('parameter', {}).get('value', {})
                    contract_address = parameter.get('contract_address')
                    
                    # Проверяем, что это наш USDT контракт
                    if contract_address == config.USDT_CONTRACT_ADDRESS:
                        data = parameter.get('data')
                        if data and len(data) >= 8:
                            # Парсим transfer данные
                            method = data[:8]
                            if method == 'a9059cbb':  # transfer method signature
                                # Извлекаем адрес получателя и сумму
                                to_address = '41' + data[32:72]  # добавляем префикс
                                amount_hex = data[72:136]
                                
                                # Конвертируем hex в decimal
                                amount = int(amount_hex, 16) / 1000000  # USDT имеет 6 decimals
                                
                                return {
                                    'tx_hash': tx_hash,
                                    'to_address': to_address,
                                    'amount': amount,
                                    'timestamp': transaction.get('block_timestamp', 0),
                                    'block_number': transaction.get('block_number', 0)
                                }
            
            return None
            
        except Exception as e:
            print(f"Ошибка парсинга TRC20 transfer: {e}")
            return None
    
    def check_new_transactions(self, wallet_address: str, last_check_time: int = None) -> List[Dict]:
        """Проверить новые транзакции с последней проверки"""
        try:
            transactions = self.get_trc20_transactions(wallet_address, limit=100)
            new_transfers = []
            
            for tx in transactions:
                tx_time = tx.get('block_timestamp', 0)
                
                # Если указано время последней проверки, фильтруем
                if last_check_time and tx_time <= last_check_time:
                    continue
                
                # Парсим transfer
                transfer_data = self.parse_trc20_transfer(tx)
                if transfer_data:
                    new_transfers.append(transfer_data)
            
            return new_transfers
            
        except Exception as e:
            print(f"Ошибка проверки новых транзакций: {e}")
            return []
    
    def validate_address(self, address: str) -> bool:
        """Валидация Tron адреса"""
        try:
            # Базовая проверка формата
            if not address or len(address) != 34:
                return False
            
            if not address.startswith('T'):
                return False
            
            # Дополнительная проверка через API
            account_info = self.get_account_info(address)
            return account_info is not None
            
        except Exception as e:
            print(f"Ошибка валидации адреса: {e}")
            return False
    
    def get_balance(self, address: str) -> float:
        """Получить баланс USDT для адреса"""
        try:
            # Используем TronScan API (более надежный)
            url = f"https://apilist.tronscanapi.com/api/account?address={address}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Ищем USDT в trc20token_balances
                trc20_balances = data.get('trc20token_balances', [])
                
                for token in trc20_balances:
                    if token.get('tokenId') == config.USDT_CONTRACT_ADDRESS:
                        # USDT имеет 6 знаков после запятой
                        balance = float(token.get('balance', 0)) / 1000000
                        return balance
                
                return 0.0
            else:
                print(f"Ошибка TronScan API: {response.status_code}")
                # Попробуем альтернативный метод через TronGrid
                return self._get_balance_from_trongrid(address)
                
        except Exception as e:
            print(f"Ошибка получения баланса: {e}")
            return 0.0
    
    def _get_balance_from_trongrid(self, address: str) -> float:
        """Альтернативный метод через TronGrid API"""
        try:
            # Используем TronGrid API
            url = f"{self.api_url}/v1/accounts/{address}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Ищем USDT в data
                if 'data' in data and isinstance(data['data'], list):
                    for item in data['data']:
                        if item.get('contract_address') == config.USDT_CONTRACT_ADDRESS:
                            balance = float(item.get('balance', 0)) / 1000000
                            return balance
                
                return 0.0
            else:
                print(f"Ошибка TronGrid API: {response.status_code}")
                return 0.0
                
        except Exception as e:
            print(f"Ошибка TronGrid API: {e}")
            return 0.0
    
    def _get_balance_from_transactions(self, address: str) -> float:
        """Альтернативный метод получения баланса через анализ транзакций"""
        try:
            # Получаем все транзакции USDT
            url = f"{self.api_url}/v1/accounts/{address}/transactions/trc20"
            params = {
                'limit': 200,  # Получаем больше транзакций для точного расчета
                'contract_address': config.USDT_CONTRACT_ADDRESS
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                transactions = data.get('data', [])
                
                balance = 0.0
                
                for tx in transactions:
                    # Проверяем, что это USDT транзакция
                    if tx.get('token_info', {}).get('contract_address') == config.USDT_CONTRACT_ADDRESS:
                        value = float(tx.get('value', 0)) / 1000000  # USDT имеет 6 знаков
                        
                        # Если это входящая транзакция
                        if tx.get('to') == address:
                            balance += value
                        # Если это исходящая транзакция
                        elif tx.get('from') == address:
                            balance -= value
                
                return max(0.0, balance)  # Баланс не может быть отрицательным
            else:
                print(f"Ошибка получения транзакций для баланса: {response.status_code}")
                return 0.0
                
        except Exception as e:
            print(f"Ошибка альтернативного получения баланса: {e}")
            return 0.0
    
    def get_usdt_balance(self, address: str) -> float:
        """Получить баланс USDT для адреса (алиас для get_balance)"""
        return self.get_balance(address)
    
    def get_new_transfers(self, address: str) -> List[Dict]:
        """Получить новые TRC20 переводы для адреса"""
        try:
            # Получаем последние транзакции
            transactions = self.get_trc20_transactions(address, limit=10)
            new_transfers = []
            
            for tx in transactions:
                # Проверяем, что это входящая транзакция
                if tx.get('to') == address:
                    transfer = {
                        'tx_hash': tx.get('transaction_id', ''),
                        'amount': float(tx.get('value', 0)) / 1000000,  # USDT имеет 6 знаков
                        'currency': 'USDT',
                        'from': tx.get('from', ''),
                        'to': tx.get('to', ''),
                        'timestamp': tx.get('block_timestamp', 0)
                    }
                    new_transfers.append(transfer)
            
            return new_transfers
            
        except Exception as e:
            print(f"Ошибка получения новых переводов: {e}")
            return []

