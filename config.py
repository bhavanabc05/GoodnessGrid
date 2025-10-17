"""
Database Configuration File
Contains all database connection settings
"""

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',        # Your MySQL server address
    'user': 'root',             # Your MySQL username (change if different)
    'password': 'bhavana@123', # YOUR MySQL password - CHANGE THIS!
    'database': 'GoodnessGrid_db',
    'port': 3306                # Default MySQL port
}

# Flask Secret Key (for sessions)
SECRET_KEY = 'your-super-secret-key-change-in-production'

# Application Settings
DEBUG = True  # Set to False in production
PORT = 5000