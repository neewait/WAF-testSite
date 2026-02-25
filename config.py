import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-prod!'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///data/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Настройки для тестирования уязвимостей (не включать в prod!)
    DEBUG = True
    SHOW_SQL_QUERIES = True