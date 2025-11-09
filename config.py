# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ================= Database Configuration =================
DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME'),
    'port': 3306
}

# ================= Flask Settings =================
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
DEBUG = True
PORT = 5000

# ================= Upload Configuration =================
UPLOAD_FOLDER = 'static/uploads/donations'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# ================= Email Configuration =================
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

# ================= Base URL =================
BASE_URL = 'http://127.0.0.1:5000'
