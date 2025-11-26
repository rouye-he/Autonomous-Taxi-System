from app.extensions import db
from datetime import datetime
from sqlalchemy import Numeric

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True)
    real_name = db.Column(db.String(50))
    phone = db.Column(db.String(20), unique=True)
    gender = db.Column(db.Enum('男', '女', '其他'))
    birth_date = db.Column(db.Date)
    id_card = db.Column(db.String(20))
    credit_score = db.Column(db.Integer, default=100)
    balance = db.Column(Numeric(10, 2), default=0.00)
    registration_time = db.Column(db.DateTime)
    registration_city = db.Column(db.String(50))
    registration_channel = db.Column(db.String(50))
    tags = db.Column(db.String(255))
    status = db.Column(db.Enum('正常', '禁用', '注销'), default='正常')
    last_login_time = db.Column(db.DateTime)
    avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'real_name': self.real_name,
            'phone': self.phone,
            'gender': self.gender,
            'birth_date': self.birth_date.strftime('%Y-%m-%d') if self.birth_date else None,
            'id_card': self.id_card,
            'credit_score': self.credit_score,
            'balance': float(self.balance) if self.balance is not None else 0.00,
            'registration_time': self.registration_time.strftime('%Y-%m-%d %H:%M:%S') if self.registration_time else None,
            'registration_city': self.registration_city,
            'registration_channel': self.registration_channel,
            'tags': self.tags,
            'status': self.status,
            'last_login_time': self.last_login_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_login_time else None,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        } 