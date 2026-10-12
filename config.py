import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MySQL Database Settings
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'hotel_management_db')
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'hotel-management-secret-key-2026')
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
