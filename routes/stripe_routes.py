"""
Module pour la gestion des paiements avec Stripe
"""
import os
import json
import stripe
from flask import Blueprint, redirect, request, jsonify, url_for, session, current_app, render_template
from flask_login import login_required, current_user
from extensions import db
from models import User
from datetime import datetime, timedelta

# Configuration de Stripe avec la clé secrète
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Création du blueprint
stripe_bp = Blueprint('stripe', __name__, url_prefix='/stripe')

# Prix des crédits (en centimes)
CREDIT_PRICES = {
    "credit_pack_5": {
        "price": 500,  # 5€
        "credits": 5,
        "name": "Pack 5 crédits"
    },
    "credit_pack_20": {
        "price": 1500,  # 15€
        "credits": 20,
        "name": "Pack 20 crédits"
    },
    "credit_pack_50": {
        "price": 3000,  # 30€
        "credits": 50,
        "name": "Pack 50 crédits"
    }
}

# Mapping des plans vers les price_id Stripe (à personnaliser avec tes vrais price_id)
PLAN_PRICE_IDS = {
    'starter': 'prod_SGmayPL1kHDAGz',  # Remplace par ton vrai price_id Stripe
    'pro': 'prod_SGma3r4XbhVfoP',         # Remplace par ton vrai price_id Stripe
    'studio': 'prod_SGmaePMKrPBqyG',   # Remplace par ton vrai price_id Stripe
}

@stripe_bp.route('/create-checkout-session/<pack_id>', methods=['POST'])
@login_required
def create_checkout_session(pack_id):
    """
    Crée une session de paiement Stripe pour l'achat de crédits
    """
    # Vérifier que le pack existe
    if pack_id not in CREDIT_PRICES:
        return jsonify({"error": "Pack de crédits invalide"}), 400
    
    pack = CREDIT_PRICES[pack_id]
    
    # Déterminer le domaine pour les redirections
    YOUR_DOMAIN = request.host_url.rstrip('/')
    
    try:
        # Créer la session de paiement Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': pack["name"],
                            'description': f'{pack["credits"]} crédits pour Masterify',
                        },
                        'unit_amount': pack["price"],
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                'user_id': current_user.id,
                'credits': pack["credits"],
                'pack_id': pack_id
            },
            mode='payment',
            success_url=YOUR_DOMAIN + url_for('stripe.payment_success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=YOUR_DOMAIN + url_for('stripe.payment_cancel'),
        )
        
        # Rediriger vers la page de paiement Stripe
        return redirect(checkout_session.url, code=303)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@stripe_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """
    Webhook pour recevoir les événements Stripe
    """
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    try:
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        event = None
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            data = json.loads(payload)
            event = {"type": data.get("type"), "data": data}
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session.get("metadata", {}).get("user_id")
            credits = session.get("metadata", {}).get("credits")
            pack_id = session.get("metadata", {}).get("pack_id")
            if user_id and credits:
                user = User.query.get(int(user_id))
                if user:
                    user.add_credits(int(credits))
                    # Attribution du plan et date de renouvellement fictive (30 jours)
                    if pack_id:
                        user.plan = pack_id
                        user.plan_renewal = datetime.utcnow() + timedelta(days=30)
                    db.session.commit()
                    current_app.logger.info(f"Added {credits} credits and plan {pack_id} to user {user_id}")
        return jsonify({"status": "success"})
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 400

@stripe_bp.route('/success')
@login_required
def payment_success():
    """
    Page de succès après un paiement
    """
    session_id = request.args.get('session_id')
    
    # Vérifier la session si un ID est fourni
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            # Vérifier que la session appartient à l'utilisateur actuel
            if str(current_user.id) == session.metadata.get('user_id'):
                credits = int(session.metadata.get('credits', 0))
                # Ajouter les crédits (au cas où le webhook n'a pas fonctionné)
                if session.payment_status == 'paid':
                    current_user.add_credits(credits)
                    db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error retrieving session: {str(e)}")
    
    return render_template('payment_success.html')

@stripe_bp.route('/cancel')
@login_required
def payment_cancel():
    """
    Page d'annulation de paiement
    """
    return render_template('payment_cancel.html')

@stripe_bp.route('/checkout')
@login_required
def checkout():
    """
    Crée une session Stripe pour un abonnement mensuel (Starter, Pro, Studio)
    """
    plan = request.args.get('plan')
    if plan not in PLAN_PRICE_IDS:
        return jsonify({'error': 'Invalid plan'}), 400

    price_id = PLAN_PRICE_IDS[plan]
    YOUR_DOMAIN = request.host_url.rstrip('/')

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            metadata={
                'user_id': current_user.id,
                'pack_id': plan
            },
            success_url=YOUR_DOMAIN + url_for('stripe.payment_success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=YOUR_DOMAIN + url_for('stripe.payment_cancel'),
            customer_email=current_user.email,
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return jsonify({'error': str(e)}), 500