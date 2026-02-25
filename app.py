#!/usr/bin/env python3
"""
SecureTest App — тестовое приложение для пентеста с WAF
Содержит намеренные уязвимости для тестирования ModSecurity CRS
"""

import os
import hashlib
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, Permission, AuditLog, SensitiveData

app = Flask(__name__)
app.config.from_object(Config)

# Инициализация расширений
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 🔐 Загрузка пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 📝 Декоратор для логирования действий
def log_action(action, resource=None, status='success'):
    """Записывает действие в аудит-лог"""
    log = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        resource=resource,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')[:255],
        status=status
    )
    db.session.add(log)
    db.session.commit()

# 🔐 Декоратор проверки прав доступа к вкладке
def require_tab_permission(tab_name):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            # Администраторы имеют доступ ко всему
            if current_user.role == 'admin':
                return f(*args, **kwargs)
            
            # Проверяем права оператора
            perm = Permission.query.filter_by(
                user_id=current_user.id,
                tab_name=tab_name,
                can_view=True
            ).first()
            
            if perm:
                log_action(f'view_{tab_name}', resource=tab_name)
                return f(*args, **kwargs)
            
            log_action(f'denied_{tab_name}', resource=tab_name, status='blocked')
            flash('Доступ запрещён', 'error')
            return redirect(url_for('dashboard'))
        return wrapped
    return decorator

# 🔐 Инициализация БД с тестовыми данными
def init_db():
    with app.app_context():
        db.create_all()
        
        # Создаём администратора, если нет
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@securetest.local',
                password_hash=generate_password_hash('Admin@123!'),
                role='admin',
                api_key=secrets.token_hex(32),
                ssn='ADMIN-001-SECRET'
            )
            db.session.add(admin)
            
            # Создаём операторов
            for i in range(1, 4):
                operator = User(
                    username=f'operator{i}',
                    email=f'op{i}@securetest.local',
                    password_hash=generate_password_hash(f'Op{i}pass!'),
                    role='operator',
                    api_key=secrets.token_hex(32),
                    ssn=f'EMP-{1000+i}-DATA'
                )
                db.session.add(operator)
            
            # 🔐 Чувствительные данные для тестирования атак
            sensitive_items = [
                {'type': 'financial', 'value': 'ENCRYPTED:cc_data_vault_2024', 'level': 'critical'},
                {'type': 'personal', 'value': 'ENCRYPTED:employee_records_db', 'level': 'confidential'},
                {'type': 'config', 'value': 'ENCRYPTED:api_master_keys', 'level': 'top-secret'},
            ]
            for item in sensitive_items:
                data = SensitiveData(
                    owner_id=1,
                    data_type=item['type'],
                    encrypted_value=item['value'],
                    access_level=item['level']
                )
                db.session.add(data)
            
            db.session.commit()
            print("✅ База данных инициализирована с тестовыми данными")

# ==================== ROUTES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        # 🔍 Уязвимость для тестирования: логирование паролей в plain text (не делать в prod!)
        log_action('login_attempt', resource=username, status='failed' if not user or not check_password_hash(user.password_hash, password) else 'success')
        
        if user and check_password_hash(user.password_hash, password) and user.is_active:
            login_user(user)
            session.permanent = True
            log_action('login_success', resource=username)
            return redirect(url_for('dashboard'))
        
        flash('Неверные учётные данные', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    log_action('logout', resource=current_user.username)
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Получаем доступные вкладки для пользователя
    if current_user.role == 'admin':
        tabs = [
            {'name': 'home', 'label': 'Главная', 'icon': '🏠'},
            {'name': 'reports', 'label': 'Отчёты', 'icon': '📊'},
            {'name': 'analytics', 'label': 'Аналитика', 'icon': '📈'},
            {'name': 'admin', 'label': 'Администрирование', 'icon': '⚙️', 'is_group': True, 'children': [
                {'name': 'settings', 'label': 'Настройки', 'icon': '🔧'},
                {'name': 'audit-logs', 'label': 'Логи событий', 'icon': '📋'},
                {'name': 'user-management', 'label': 'Пользователи', 'icon': '👥'},
                {'name': 'permissions', 'label': 'Права доступа', 'icon': '🔐'},
            ]},
            {'name': 'sensitive', 'label': 'Конфиденциально', 'icon': '🔒'},
        ]
    else:
        # Оператор видит только выданные права
        perms = Permission.query.filter_by(user_id=current_user.id, can_view=True).all()
        allowed_tabs = [p.tab_name for p in perms]
        
        all_tabs = [
            {'name': 'home', 'label': 'Главная', 'icon': '🏠'},
            {'name': 'reports', 'label': 'Отчёты', 'icon': '📊'},
            {'name': 'analytics', 'label': 'Аналитика', 'icon': '📈'},
            {'name': 'tasks', 'label': 'Задачи', 'icon': '✅'},
        ]
        tabs = [t for t in all_tabs if t['name'] in allowed_tabs or t['name'] == 'home']
    
    return render_template('dashboard.html', tabs=tabs)

# 🔐 Админ-панель: управление пользователями
@app.route('/admin/users')
@login_required
@require_tab_permission('user-management')
def admin_users():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# 🔐 Админ-панель: выдача прав
@app.route('/admin/permissions', methods=['GET', 'POST'])
@login_required
@require_tab_permission('permissions')
def admin_permissions():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        tab_name = request.form.get('tab_name')
        can_view = 'view' in request.form
        can_edit = 'edit' in request.form
        
        # Проверяем, что админ не выдаёт права на админ-панель операторам без проверки
        perm = Permission.query.filter_by(user_id=user_id, tab_name=tab_name).first()
        if perm:
            perm.can_view = can_view
            perm.can_edit = can_edit
        else:
            perm = Permission(
                user_id=user_id,
                tab_name=tab_name,
                can_view=can_view,
                can_edit=can_edit,
                granted_by=current_user.id
            )
            db.session.add(perm)
        
        db.session.commit()
        log_action('permission_granted', resource=f'user:{user_id}:tab:{tab_name}')
        flash('Права обновлены', 'success')
        return redirect(url_for('admin_permissions'))
    
    operators = User.query.filter_by(role='operator').all()
    available_tabs = ['reports', 'analytics', 'tasks', 'settings']
    return render_template('admin/permissions.html', operators=operators, tabs=available_tabs)

# 🔐 Админ-панель: просмотр логов
@app.route('/admin/logs')
@login_required
@require_tab_permission('audit-logs')
def admin_logs():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    
    # 🔍 Уязвимость для тестирования: SQL-инъекция через параметр filter
    # (в реальном приложении использовать параметризованные запросы!)
    filter_action = request.args.get('filter', '')
    if filter_action:
        # ⚠️ НАМЕРЕННАЯ УЯЗВИМОСТЬ для тестирования WAF
        logs = AuditLog.query.filter(AuditLog.action.like(f'%{filter_action}%')).all()
    else:
        logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    
    return render_template('admin/logs.html', logs=logs)

# 🔐 Страница с чувствительными данными (тест IDOR/прямой доступ)
@app.route('/api/sensitive/<int:data_id>')
@login_required
def get_sensitive_data(data_id):
    """
    🔍 Уязвимость для тестирования: Insecure Direct Object Reference (IDOR)
    Любой авторизованный пользователь может получить данные по ID без проверки владельца
    """
    data = SensitiveData.query.get(data_id)
    if not data:
        return jsonify({'error': 'Not found'}), 404
    
    # ⚠️ НАМЕРЕННО: не проверяем, что пользователь имеет право на эти данные
    # В реальном приложении здесь должна быть проверка owner_id или access_level
    
    log_action('access_sensitive_data', resource=f'id:{data_id}', status='warning')
    
    return jsonify({
        'id': data.id,
        'type': data.data_type,
        'value': data.encrypted_value,  # "Зашифрованные" данные
        'level': data.access_level
    })

# 🔍 Уязвимый endpoint для тестирования XSS
@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    # ⚠️ НАМЕРЕННО: вывод без экранирования для тестирования XSS
    return render_template('search.html', query=query, results=[])

# 🔍 Уязвимый endpoint для тестирования SQLi в форме
@app.route('/api/users/search', methods=['POST'])
@login_required
def api_search_users():
    username = request.form.get('username', '')
    # ⚠️ НАМЕРЕННАЯ УЯЗВИМОСТЬ: конкатенация в SQL-запросе
    # В реальном приложении использовать параметризованные запросы!
    if username:
        query = f"SELECT * FROM user WHERE username LIKE '%{username}%'"  # ❌ Уязвимо!
        users = db.session.execute(query).fetchall()
    else:
        users = []
    return jsonify([{'id': u.id, 'username': u.username} for u in users])

# Health check для WAF
@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'securetest-app'}), 200

# Обработчики ошибок
@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    log_action('server_error', resource=str(e), status='error')
    return render_template('errors/500.html'), 500

if __name__ == '__init_main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)