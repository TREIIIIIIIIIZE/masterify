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
def dashboard():
    """User dashboard with mastered files and credits"""
    # Version de démonstration sans authentification
    # Créer un utilisateur de démonstration pour l'affichage
    class DemoUser:
        def __init__(self):
            self.username = "DemoUser"
            self.credits = 5
            self.email = "demo@example.com"
    
    demo_user = DemoUser()
    return render_template('dashboard.html', user=demo_user)
