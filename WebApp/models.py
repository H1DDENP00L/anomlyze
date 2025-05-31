# WebApp/models.py
from .app import db 
from passlib.hash import bcrypt 
from datetime import datetime, timezone 



class User(db.Model):
    __tablename__ = 'users' 

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) 
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    

    def __init__(self, username, email, password):
        self.username = username
        self.email = email.lower() 
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password):
        return bcrypt.verify(password, self.password_hash)

    def __repr__(self):
        return f'<User {self.username}>'

class Anomaly(db.Model):
    __tablename__ = 'anomalies'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    
    timestamp_detected = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    source_type = db.Column(db.String(10), nullable=False) # 'file' or 'rtsp'
    source_identifier = db.Column(db.Text, nullable=False) # Имя файла или RTSP URL
    
    image_url = db.Column(db.Text, nullable=False) 

    detected_class = db.Column(db.String(50), nullable=True) 
    
    description = db.Column(db.Text, nullable=True) # описание (мб в будущем пользователь добавит)
    is_reviewed = db.Column(db.Boolean, default=False, nullable=False) # Просмотрена ли аномалия

    user_who_triggered = db.relationship('User', backref=db.backref('triggered_anomalies', lazy='dynamic'))

    def __repr__(self):
        return f'<Anomaly {self.id} - {self.source_identifier} at {self.timestamp_detected}>'