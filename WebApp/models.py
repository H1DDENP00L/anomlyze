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

