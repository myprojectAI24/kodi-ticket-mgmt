# models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tickets = db.relationship('Ticket', backref='profile', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Profile {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'tickets': [ticket.to_dict() for ticket in self.tickets]
        }

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)
    lock_code = db.Column(db.String(4), nullable=False, unique=True)
    length = db.Column(db.Integer, nullable=False)  # in minutes
    is_active = db.Column(db.Boolean, default=True)  # Green when True, Red when False
    used_at = db.Column(db.DateTime, nullable=True)  # When the ticket was used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Ticket {self.lock_code} - Profile {self.profile_id}>'

    @staticmethod
    def generate_unique_pin():
        """Generate a unique 4-digit PIN"""
        max_attempts = 100
        for _ in range(max_attempts):
            pin = str(random.randint(0, 9999)).zfill(4)
            if not Ticket.query.filter_by(lock_code=pin).first():
                return pin
        raise ValueError("Could not generate unique PIN after maximum attempts")

    def to_dict(self):
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'profile_name': self.profile.name,
            'lock_code': self.lock_code,
            'length': self.length,
            'is_active': self.is_active,
            'used_at': self.used_at.strftime('%Y-%m-%d %H:%M:%S') if self.used_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }