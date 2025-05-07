from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    credits = db.Column(db.Integer, default=1)  # New users get 1 free credit
    mastered_files = db.relationship('MasteredFile', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def use_credit(self):
        if self.credits > 0:
            self.credits -= 1
            return True
        return False
    
    def add_credits(self, amount):
        self.credits += amount

class MasteredFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    processed_filename = db.Column(db.String(255), nullable=False)
    preset_used = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    duration = db.Column(db.Float)  # Duration in seconds
    download_count = db.Column(db.Integer, default=0)
    
    def increment_download(self):
        self.download_count += 1
