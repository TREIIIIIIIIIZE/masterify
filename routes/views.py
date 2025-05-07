from flask import Blueprint, render_template, redirect, url_for, session
from flask_login import login_required, current_user

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Home page with parallax effect"""
    return render_template('index.html')

@views_bp.route('/upload')
def upload():
    """Upload page for audio mastering"""
    return render_template('upload.html')

@views_bp.route('/pricing')
def pricing():
    """Pricing page for credits"""
    return render_template('pricing.html')

@views_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@views_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@views_bp.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)
