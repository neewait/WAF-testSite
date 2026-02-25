from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Таблица пользователей
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='operator')  # admin / operator
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с правами доступа
    permissions = db.relationship('Permission', backref='user', lazy=True)
    
    # 🔐 Чувствительные данные (для тестирования атак)
    api_key = db.Column(db.String(64), unique=True)  # Симуляция API-ключа
    ssn = db.Column(db.String(20))  # Симуляция персонального номера
    
    def __repr__(self):
        return f'<User {self.username}>'

# Таблица прав доступа (RBAC)
class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tab_name = db.Column(db.String(50), nullable=False)  # 'reports', 'analytics', etc.
    can_view = db.Column(db.Boolean, default=True)
    can_edit = db.Column(db.Boolean, default=False)
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)

# Таблица событий/логов для просмотра админом
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(100))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    status = db.Column(db.String(20))  # success / failed / blocked
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuditLog {self.action} by user {self.user_id}>'

# 🔐 Таблица с "чувствительными данными" для тестирования атак
class SensitiveData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    data_type = db.Column(db.String(50))  # 'financial', 'personal', 'config'
    encrypted_value = db.Column(db.Text)  # Симуляция зашифрованных данных
    access_level = db.Column(db.String(20), default='confidential')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)