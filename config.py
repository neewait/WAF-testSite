import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-prod!'
    
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/securetest.db'
    
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False}
    }
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    DEBUG = True
    SHOW_SQL_QUERIES = True
