import os
from flask import Blueprint, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from app import app, db
from models import User

auth_bp = Blueprint('auth', __name__)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with one free credit"""
    data = request.get_json()
    
    # Check if user already exists
    if db.session.query(User).filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    if db.session.query(User).filter_by(username=data['username']).first():
        return jsonify({'success': False, 'message': 'Username already taken'}), 400
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        credits=1  # One free credit for new users
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Auto login the user after registration
    login_user(user)
    
    return jsonify({
        'success': True, 
        'message': 'Registration successful', 
        'user': {
            'id': user.id,
            'username': user.username,
            'credits': user.credits
        }
    })

@auth_bp.route('/login', methods=['POST'])
def login():
    """Log in a user"""
    data = request.get_json()
    
    # Find user by email
    user = db.session.query(User).filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    
    login_user(user)
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'credits': user.credits
        }
    })

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@auth_bp.route('/user')
@login_required
def get_user():
    """Get the current user's info"""
    return jsonify({
        'success': True,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'credits': current_user.credits
        }
    })

@auth_bp.route('/add-credits', methods=['POST'])
@login_required
def add_credits():
    """Add credits to user account - this would connect to a payment processor in production"""
    data = request.get_json()
    credit_amount = int(data.get('amount', 1))
    
    current_user.add_credits(credit_amount)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Added {credit_amount} credits',
        'credits': current_user.credits
    })
