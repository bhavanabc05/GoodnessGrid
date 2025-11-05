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

# Upload Configuration
UPLOAD_FOLDER = 'static/uploads/donations'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

# Email Configuration (Gmail SMTP)
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'bhavanabc05@gmail.com'  # Replace with your Gmail
MAIL_PASSWORD = 'ktdl kyns vhin rtum'      # Replace with App Password
MAIL_DEFAULT_SENDER = 'bhavanabc05@gmail.com'

# Base URL for verification links
BASE_URL = 'http://127.0.0.1:5000'