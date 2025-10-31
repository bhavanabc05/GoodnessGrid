# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# MySQL Database Configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME'),
    'port': 3306
}

# Flask Secret Key (for sessions)
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')

# Application Settings
DEBUG = True
PORT = 5000