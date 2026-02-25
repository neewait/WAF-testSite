#!/usr/bin/env python3
"""Скрипт инициализации базы данных"""

import sys
sys.path.insert(0, '/opt/app')

from app import app, init_db

if __name__ == '__main__':
    with app.app_context():
        init_db()
    print("✅ База данных готова")