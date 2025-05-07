import os
from flask import Blueprint, request, jsonify, session, redirect, url_for, flash, render_template
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with one free credit"""
    try:
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
    except Exception as e:
        print('Erreur lors de l\'inscription:', e)
        return jsonify({'success': False, 'message': f'Erreur serveur: {str(e)}'}), 500

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

@auth_bp.route('/login_page')
def login_page():
    """Page de connexion/inscription"""
    from flask import render_template, request
    next_url = request.args.get('next', '')
    return render_template('auth.html', next=next_url)

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

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

@auth_bp.route('/update', methods=['POST'])
@login_required
def update_account():
    data = request.get_json()
    user = current_user
    if 'username' in data and data['username']:
        user.username = data['username']
    if 'email' in data and data['email']:
        user.email = data['email']
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    db.session.commit()
    return jsonify({'success': True, 'message': 'Account updated'})
