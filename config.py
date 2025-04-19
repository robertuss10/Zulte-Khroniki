import os

# Bot Configuration
TOKEN = os.getenv('DISCORD_TOKEN', '')
COMMAND_PREFIX = '/'

# Anti-spam Configuration
COOLDOWN_TIME = 6  # seconds
SPECIFIC_QUOTE_COOLDOWN = 15 * 60  # 15 minutes in seconds

# Personalities
PERSONALITIES = {
    'wgg': 'Weterani Gier Gacha',
    'wriu': 'Wriu',
    'zultan': 'Zultan',
    'arizonka': 'Arizonka',
    'arrow': 'Arrow',
    'aruel': 'Aruel',
    'murzyn': 'Murzyn'  # Assuming this is the seventh personality
}

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# Web Dashboard Configuration
SECRET_KEY = os.getenv('SESSION_SECRET', 'zulte-kroniki-secret-key')
HOST = '0.0.0.0'
PORT = 5000

# Style Configuration
COLORS = {
    'primary': '#FFD700',  # golden yellow
    'secondary': '#FFF7E6',  # soft cream
    'accent': '#FFB300',  # warm amber
    'text': '#2C2F33'  # discord dark
}

# Quotes Files Path
QUOTES_DIRECTORY = 'attached_assets'

# API endpoint for the bot
API_BASE_URL = f'http://127.0.0.1:{PORT}/api'
