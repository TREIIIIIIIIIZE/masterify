from app import app
from models import User, db
from datetime import datetime, timedelta

# Informations du compte développeur
DEV_USERNAME = 'bryanlerustre'
DEV_EMAIL = 'dev@masterify.com'  # Remplacez par votre email réel
DEV_PASSWORD = 'masterdev2024'    # Changez ce mot de passe

def main():
    with app.app_context():
        # Vérifier si le compte existe déjà
        user = User.query.filter_by(username=DEV_USERNAME).first()
        
        if user:
            print(f"Le compte {DEV_USERNAME} existe déjà.")
            # Mise à jour du compte
            user.credits = 999999
            user.plan = 'studio'
            user.plan_renewal = datetime.utcnow() + timedelta(days=3650)  # 10 ans
            db.session.commit()
            print(f"Le compte a été mis à jour avec des crédits illimités et un plan Studio.")
        else:
            # Création du compte développeur
            user = User(
                username=DEV_USERNAME,
                email=DEV_EMAIL,
                provider='email',
                credits=999999,
                plan='studio',
                plan_renewal=datetime.utcnow() + timedelta(days=3650)  # 10 ans
            )
            user.set_password(DEV_PASSWORD)
            db.session.add(user)
            db.session.commit()
            print(f"Le compte développeur {DEV_USERNAME} a été créé avec des crédits illimités.")
        
        print(f"Utilisateur: {user.username}")
        print(f"Email: {user.email}")
        print(f"Crédits: {user.credits}")
        print(f"Plan: {user.plan}")
        print(f"Expiration: {user.plan_renewal}")

if __name__ == "__main__":
    main() 