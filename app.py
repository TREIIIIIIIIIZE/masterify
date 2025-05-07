import os
import logging
import json
from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.discord import make_discord_blueprint, discord
from dotenv import load_dotenv
from flask_migrate import Migrate

# Import local modules
from extensions import db, login_manager
from models import User, MasteredFile
from routes.auth import auth_bp
from routes.views import views_bp
from routes.stripe_routes import stripe_bp

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# DEBUG : Affichage des variables d'environnement OAuth
print('GOOGLE_OAUTH_CLIENT_ID:', os.environ.get('GOOGLE_OAUTH_CLIENT_ID'))
print('GOOGLE_OAUTH_CLIENT_SECRET:', os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET'))
print('DISCORD_CLIENT_ID:', os.environ.get('DISCORD_CLIENT_ID'))
print('DISCORD_CLIENT_SECRET:', os.environ.get('DISCORD_CLIENT_SECRET'))

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///masterify.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager.init_app(app)
login_manager.login_view = 'auth.login_page'

@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access attempts by redirecting to login page with next parameter"""
    return redirect(url_for('auth.login_page', next=request.path))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Enable CORS
CORS(app)

# Configuration OAuth pour Google
google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_OAUTH_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET'),
    scope=["profile", "email"],
    redirect_url="/login/google/callback"
)

# Configuration OAuth pour Discord
discord_bp = make_discord_blueprint(
    client_id=os.environ.get('DISCORD_CLIENT_ID'),
    client_secret=os.environ.get('DISCORD_CLIENT_SECRET'),
    scope=["identify", "email"],
    redirect_url="/login/discord/callback"
)

app.register_blueprint(google_bp, url_prefix="/login/google")
app.register_blueprint(discord_bp, url_prefix="/login/discord")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth')
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('auth.html')

# Routes pour l'authentification OAuth
@app.route('/login/google/callback')
def google_callback():
    if not google.authorized:
        return redirect(url_for('google.login'))
    
    resp = google.get('/oauth2/v2/userinfo')
    if resp.ok:
        user_info = resp.json()
        
        # Vérifier si l'utilisateur existe déjà
        user = User.query.filter_by(email=user_info['email']).first()
        
        if not user:
            # Créer un nouvel utilisateur
            user = User(
                email=user_info['email'],
                username=user_info.get('name', user_info['email'].split('@')[0]),
                provider='google',
                provider_id=user_info['id'],
                credits=1  # Un crédit gratuit pour les nouveaux utilisateurs
            )
            db.session.add(user)
            db.session.commit()
        
        # Connecter l'utilisateur
        login_user(user)
        flash('Connexion réussie via Google!')
        
        # Rediriger vers la page d'accueil ou la dernière page visitée
        next_page = session.get('next', url_for('index'))
        return redirect(next_page)
    
    flash('Échec de la connexion via Google. Veuillez réessayer.')
    return redirect(url_for('auth'))

@app.route('/login/discord/callback')
def discord_callback():
    if not discord.authorized:
        return redirect(url_for('discord.login'))
    
    resp = discord.get('/api/users/@me')
    if resp.ok:
        user_info = resp.json()
        
        # Vérifier si l'utilisateur existe déjà
        user = User.query.filter_by(email=user_info['email']).first()
        
        if not user:
            # Créer un nouvel utilisateur
            user = User(
                email=user_info['email'],
                username=user_info.get('username', user_info['email'].split('@')[0]),
                provider='discord',
                provider_id=user_info['id'],
                credits=1  # Un crédit gratuit pour les nouveaux utilisateurs
            )
            db.session.add(user)
            db.session.commit()
        
        # Connecter l'utilisateur
        login_user(user)
        flash('Connexion réussie via Discord!')
        
        # Rediriger vers la page d'accueil ou la dernière page visitée
        next_page = session.get('next', url_for('index'))
        return redirect(next_page)
    
    flash('Échec de la connexion via Discord. Veuillez réessayer.')
    return redirect(url_for('auth'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Create database tables
with app.app_context():
    db.create_all()
    
    # Enregistrer les blueprints
    app.register_blueprint(views_bp)
    app.register_blueprint(stripe_bp)
    app.register_blueprint(auth_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
