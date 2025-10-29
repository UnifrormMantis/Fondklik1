import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Tron Configuration
TRON_API_URL = os.getenv('TRON_API_URL', 'https://api.trongrid.io')
TRON_API_KEY = os.getenv('TRON_API_KEY')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///payments.db')

# Bot Settings
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 60))  # seconds
CONFIRMATION_BLOCKS = int(os.getenv('CONFIRMATION_BLOCKS', 3))

# TRC20 Token Configuration (USDT example)
USDT_CONTRACT_ADDRESS = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # USDT TRC20

